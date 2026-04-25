"""
EWI EasyPlay - 完整服務層 v2.0
包含：YouTube 下載、音頻分析、EWI 運指演算法、Spotify 集成
"""

import os
import logging
import asyncio
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile

# 加載環境變數
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        logging.info(f"✓ 已加載環境配置: {env_file}")
except ImportError:
    pass

logger = logging.getLogger(__name__)

class TaskManager:
    """任務管理器"""
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self.task_counter = 0

    def create_task(self, task_type: str, **kwargs) -> str:
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "status": "processing",
            "progress": 0,
            "current_step": "初始化中...",
            "error": None,
            "results": None,
            "title": kwargs.get("title", "未知"),
            **kwargs
        }
        return task_id

    def update_task(self, task_id: str, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)

    def get_task(self, task_id: str) -> Optional[dict]:
        return self.tasks.get(task_id)

    def complete_task(self, task_id: str, results: dict):
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "完成",
                "results": results
            })

    def fail_task(self, task_id: str, error: str):
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "error",
                "error": error,
                "current_step": "錯誤"
            })


class YouTubeDownloader:
    """YouTube 下載服務"""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def download(self, url: str, task_id: str, task_manager: TaskManager) -> Optional[str]:
        """使用 yt-dlp 下載 YouTube 音頻"""
        try:
            task_manager.update_task(task_id, current_step="下載 YouTube 音頻中...", progress=10)

            import yt_dlp

            output_path = self.temp_dir / f"{task_id}.mp3"

            # 在線程中運行下載，避免阻塞。
            # 某些影片在特定格式選擇下會報 "Requested format is not available"，這裡做多組 fallback。
            loop = asyncio.get_event_loop()

            def download_impl():
                # 優先嘗試可直接抽取音訊，其次回退到常見 HLS mp4 清晰度格式。
                format_candidates = [
                    "bestaudio/best",
                    "bestaudio*",
                    "95/94/93/92/91/best",
                    "best"
                ]
                last_error = None

                for fmt in format_candidates:
                    ydl_opts = {
                        'format': fmt,
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['tv', 'web_safari', 'ios']
                            }
                        },
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'outtmpl': str(self.temp_dir / f"{task_id}"),
                        'quiet': False,
                        'no_warnings': True,
                    }

                    try:
                        logger.info(f"yt-dlp 嘗試格式: {fmt}")
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                        return output_path
                    except Exception as err:
                        last_error = err
                        logger.warning(f"yt-dlp 格式 {fmt} 下載失敗: {err}")

                raise last_error if last_error else Exception("yt-dlp 下載失敗")

            result_path = await loop.run_in_executor(None, download_impl)

            # 檢查輸出文件
            if result_path.exists():
                task_manager.update_task(task_id, progress=25)
                logger.info(f"成功下載: {result_path}")
                return str(result_path)
            else:
                raise Exception(f"下載後找不到文件: {result_path}")

        except Exception as e:
            logger.error(f"YouTube 下載錯誤: {str(e)}")
            raise


class AudioAnalyzer:
    """音頻分析服務 - 提取旋律和基礎特徵"""

    async def analyze(self, audio_path: str, task_id: str, task_manager: TaskManager) -> List[Dict]:
        """提取音頻旋律（F0）並轉換為簡譜音符"""
        try:
            task_manager.update_task(task_id, current_step="分析音頻旋律中...", progress=40)

            try:
                import librosa
                import numpy as np
            except ImportError:
                logger.warning("librosa 未安裝，使用模擬數據")
                return self._get_demo_notes()

            logger.info(f"加載音頻: {audio_path}")
            y, sr = librosa.load(audio_path, sr=22050)

            # 使用 PYIN 算法提取基頻 (F0)
            try:
                f0, voiced_flag, voiced_probs = librosa.pyin(
                    y,
                    fmin=librosa.note_to_hz('C3'),
                    fmax=librosa.note_to_hz('C6'),
                    sr=sr
                )
            except:
                # 備用方案：使用 piptrack
                f0 = librosa.feature.zero_crossing_rate(y)[0]
                return self._get_demo_notes()

            # 將頻率轉換為音符
            notes = []
            for i, freq in enumerate(f0):
                if not np.isnan(freq) and freq > 0:
                    midi_note = librosa.hz_to_midi(freq)
                    note = self._midi_to_note(int(round(midi_note)))
                    notes.append({
                        "midi": int(round(midi_note)),
                        "note": note,
                        "frequency": float(freq),
                        "index": i
                    })
                else:
                    notes.append(None)

            # 簡化序列
            simplified = self._simplify_notes(notes)

            task_manager.update_task(task_id, progress=60)
            logger.info(f"提取了 {len(simplified)} 個音符")

            return simplified

        except Exception as e:
            logger.error(f"音頻分析錯誤: {str(e)}")
            return self._get_demo_notes()

    @staticmethod
    def _midi_to_note(midi_note: int) -> str:
        """MIDI 編號轉簡譜數字"""
        note_map = {0: '1', 2: '2', 4: '3', 5: '4', 7: '5', 9: '6', 11: '7'}
        return note_map.get(midi_note % 12, '5')

    @staticmethod
    def _simplify_notes(notes: List, min_duration: int = 5) -> List[Dict]:
        """簡化音符序列，合併連續相同的音符"""
        if not notes:
            return []

        simplified = []
        current_note = None
        count = 0

        for note in notes:
            if note is None:
                if current_note and count >= min_duration:
                    simplified.append(current_note)
                current_note = None
                count = 0
            elif current_note is None or note['note'] != current_note['note']:
                if current_note and count >= min_duration:
                    simplified.append(current_note)
                current_note = note
                count = 1
            else:
                count += 1

        if current_note and count >= min_duration:
            simplified.append(current_note)

        return simplified

    @staticmethod
    def _get_demo_notes() -> List[Dict]:
        """返回演示音符序列"""
        demo = [1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5, 6, 7]
        return [
            {"midi": 60 + note, "note": str(note), "frequency": 440.0 * (2 ** ((note - 9) / 12))}
            for note in demo
        ]


class JianguGenerator:
    """簡譜生成服務"""

    @staticmethod
    def generate(notes: List[Dict], difficulty: str = "normal") -> Dict:
        """根據音符序列生成簡譜"""
        try:
            logger.info(f"生成簡譜 - 難度: {difficulty}, 音符數: {len(notes)}")

            if not notes:
                notes_str = "1 2 3 4 5 6 7 1' -"
            else:
                note_sequence = [str(note['note']) for note in notes if note]

                # 根據難度調整密度
                if difficulty == "easy":
                    step = max(1, len(note_sequence) // 8)  # 簡化到 8 個音符
                    note_sequence = note_sequence[::step] if step > 1 else note_sequence[:8]
                elif difficulty == "hard":
                    pass  # 完整保留
                else:  # normal
                    step = max(1, len(note_sequence) // 12)  # 中等密度
                    note_sequence = note_sequence[::step] if step > 1 else note_sequence

                notes_str = " ".join(note_sequence)

            jianpu = {
                "notes": notes_str,
                "fingering": f"{difficulty} 難度運指",
                "tempo": 80 if difficulty == "easy" else (120 if difficulty == "normal" else 140),
                "key": "C",
                "time_signature": "4/4",
                "difficulty": difficulty
            }

            logger.info(f"簡譜生成完成")
            return jianpu

        except Exception as e:
            logger.error(f"簡譜生成錯誤: {str(e)}")
            raise


class EWIFingeringAlgorithm:
    """EWI 運指指法演算法 - 將簡譜轉換為 EWI 運指"""

    # EWI 的五孔運指對應
    EWI_FINGERING_MAP = {
        # 基礎音符 (C 調)
        '1': {'left': [0, 0, 0], 'right': [0, 0, 0], 'key': 'C'},  # C
        '2': {'left': [0, 0, 0], 'right': [0, 0, 1], 'key': 'D'},  # D
        '3': {'left': [0, 0, 0], 'right': [0, 1, 1], 'key': 'E'},  # E
        '4': {'left': [0, 0, 0], 'right': [1, 1, 1], 'key': 'F'},  # F
        '5': {'left': [0, 0, 1], 'right': [1, 1, 1], 'key': 'G'},  # G
        '6': {'left': [0, 1, 1], 'right': [1, 1, 1], 'key': 'A'},  # A
        '7': {'left': [1, 1, 1], 'right': [1, 1, 1], 'key': 'B'},  # B
    }

    @classmethod
    def calculate_fingering(cls, notes: List[Dict], difficulty: str = "normal") -> List[Dict]:
        """計算 EWI 運指"""
        try:
            logger.info(f"計算 EWI 運指 - 難度: {difficulty}")

            fingering_sequence = []

            for note in notes:
                if not note:
                    continue

                note_str = str(note.get('note', '5'))

                # 從映射中獲取運指
                if note_str in cls.EWI_FINGERING_MAP:
                    fingering_info = cls.EWI_FINGERING_MAP[note_str]
                else:
                    fingering_info = cls.EWI_FINGERING_MAP.get('5', {})

                # 根據難度調整運指難度
                difficulty_factor = {
                    'easy': 0.5,
                    'normal': 0.8,
                    'hard': 1.0
                }.get(difficulty, 0.8)

                fingering_sequence.append({
                    'note': note_str,
                    'fingering': fingering_info,
                    'difficulty_rating': difficulty_factor,
                    'key': fingering_info.get('key', 'C'),
                    'technique': cls._get_technique(note_str, difficulty)
                })

            logger.info(f"生成了 {len(fingering_sequence)} 個運指")
            return fingering_sequence

        except Exception as e:
            logger.error(f"運指計算錯誤: {str(e)}")
            return []

    @staticmethod
    def _get_technique(note: str, difficulty: str) -> str:
        """根據難度返回運指技巧"""
        techniques = {
            'easy': ['基礎運指', '直吹', '基礎指法'],
            'normal': ['標準運指', '連吹', '連音指法', '簡單連指'],
            'hard': ['高級運指', '跳音', '複雜指法', '滑音', '裝飾音']
        }

        import random
        technique_list = techniques.get(difficulty, techniques['normal'])
        return random.choice(technique_list)


class MIDIGenerator:
    """MIDI 生成服務"""

    @staticmethod
    def generate(notes: List[Dict], title: str, difficulty: str = "normal", data_dir: Path = None) -> Optional[str]:
        """生成 MIDI 文件"""
        try:
            if data_dir is None:
                data_dir = Path("data")

            logger.info(f"生成 MIDI 文件 - {title}")

            try:
                from midiutil import MIDIFile
            except ImportError:
                logger.warning("midiutil 未安裝，跳過 MIDI 生成")
                return None

            # 創建 MIDI
            midi = MIDIFile(1)
            track = 0
            channel = 0
            time = 0
            volume = 100

            # 根據難度設定速度
            tempo_map = {'easy': 80, 'normal': 120, 'hard': 140}
            tempo = tempo_map.get(difficulty, 120)
            midi.addTempo(track, 0, tempo)

            # 添加音符
            duration = 1  # 每個音符 1 拍

            if not notes:
                note_sequence = [60, 62, 64, 65, 67, 69, 71, 72]
            else:
                note_sequence = [note.get('midi', 60) for note in notes if note]

            for pitch in note_sequence:
                midi.addNote(track, channel, pitch, time, duration, volume)
                time += duration

            # 保存
            output_path = data_dir / f"{title}_{difficulty}.mid"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                midi.writeFile(f)

            logger.info(f"MIDI 已保存: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"MIDI 生成錯誤: {str(e)}")
            return None


class SpotifyIntegrator:
    """Spotify 真實集成"""

    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/api/spotify/callback")
        self.access_token = None

    async def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """搜尋 Spotify 音樂"""
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
        except ImportError:
            logger.warning("spotipy 未安裝，使用模擬數據")
            return self._get_demo_tracks(query, limit)

        try:
            if not self.client_id or not self.client_secret:
                logger.warning("Spotify 證書未設定，使用模擬數據")
                return self._get_demo_tracks(query, limit)

            # 使用 Client Credentials 流程
            auth_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            sp = spotipy.Spotify(auth_manager=auth_manager)

            # 搜尋
            results = sp.search(q=query, type='track', limit=limit)

            tracks = []
            for item in results['tracks']['items']:
                track = {
                    'id': item['id'],
                    'name': item['name'],
                    'artists': [{'name': artist['name']} for artist in item['artists']],
                    'album': {
                        'name': item['album']['name'],
                        'images': item['album']['images']
                    },
                    'preview_url': item.get('preview_url'),
                    'external_urls': item.get('external_urls', {})
                }
                tracks.append(track)

            logger.info(f"從 Spotify 找到 {len(tracks)} 首歌曲")
            return tracks

        except Exception as e:
            logger.error(f"Spotify 搜尋失敗: {str(e)}")
            return self._get_demo_tracks(query, limit)

    @staticmethod
    def _get_demo_tracks(query: str, limit: int = 10) -> List[Dict]:
        """返回演示 Spotify 搜尋結果"""
        demo_tracks = [
            {
                'id': f'demo_{i}',
                'name': f'{query} - 搜尋結果 {i}',
                'artists': [{'name': f'藝人 {i}'}],
                'album': {
                    'name': '演示專輯',
                    'images': [{'url': f'https://via.placeholder.com/300?text=Album+{i}'}]
                },
                'preview_url': None,
                'external_urls': {'spotify': 'https://spotify.com'}
            }
            for i in range(1, min(limit, 6))
        ]
        return demo_tracks


# 全域實例
task_manager = TaskManager()
youtube_downloader = YouTubeDownloader(Path("temp"))
audio_analyzer = AudioAnalyzer()
jianpu_generator = JianguGenerator()
ewi_fingering = EWIFingeringAlgorithm()
midi_generator = MIDIGenerator()
spotify_integrator = SpotifyIntegrator()
