"""
EWI EasyPlay - 核心服務層
負責音頻處理、分析和簡譜生成
"""

import os
import logging
import asyncio
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile

# 日誌配置
logger = logging.getLogger(__name__)

class TaskManager:
    """任務管理器 - 追蹤異步任務進度"""
    
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self.task_counter = 0
    
    def create_task(self, task_type: str, **kwargs) -> str:
        """創建新任務"""
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
        """更新任務狀態"""
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """獲取任務狀態"""
        return self.tasks.get(task_id)
    
    def complete_task(self, task_id: str, results: dict):
        """完成任務"""
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "完成",
                "results": results
            })
    
    def fail_task(self, task_id: str, error: str):
        """標記任務失敗"""
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "error",
                "error": error,
                "current_step": "錯誤"
            })


class AudioProcessor:
    """音頻處理服務"""
    
    def __init__(self):
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    async def download_youtube(self, url: str, task_id: str, task_manager: TaskManager) -> Optional[str]:
        """下載 YouTube 音頻"""
        try:
            task_manager.update_task(task_id, current_step="下載 YouTube 音頻中...", progress=10)
            
            output_path = self.temp_dir / f"{task_id}.mp3"
            
            # 使用 yt-dlp 下載
            cmd = [
                "yt-dlp",
                "-f", "bestaudio/best",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "192",
                "-o", str(output_path),
                url
            ]
            
            # 異步執行下載
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "未知錯誤"
                logger.error(f"YouTube 下載失敗: {error_msg}")
                raise Exception(f"下載失敗: {error_msg[:100]}")
            
            if not output_path.exists():
                raise Exception("下載完成但找不到文件")
            
            task_manager.update_task(task_id, progress=25)
            logger.info(f"成功下載: {output_path}")
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"YouTube 下載錯誤: {str(e)}")
            raise
    
    async def analyze_audio(self, audio_path: str, task_id: str, task_manager: TaskManager) -> List[Dict]:
        """分析音頻，提取旋律（F0 提取）"""
        try:
            task_manager.update_task(task_id, current_step="分析音頻旋律中...", progress=40)
            
            import librosa
            import numpy as np
            
            # 加載音頻
            logger.info(f"加載音頻: {audio_path}")
            y, sr = librosa.load(audio_path, sr=None)
            
            # 提取基頻 (F0) - 使用 PYIN 算法
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=sr
            )
            
            # 將頻率轉換為音符
            notes = []
            for freq in f0:
                if not np.isnan(freq) and freq > 0:
                    # 頻率轉 MIDI 音符編號
                    midi_note = librosa.hz_to_midi(freq)
                    note = self._midi_to_note(int(round(midi_note)))
                    notes.append({
                        "midi": int(round(midi_note)),
                        "note": note,
                        "frequency": float(freq)
                    })
                else:
                    notes.append(None)
            
            # 簡化音符序列（去除相鄰重複和太短的音符）
            simplified_notes = self._simplify_notes(notes, min_frames=5)
            
            task_manager.update_task(task_id, progress=60)
            logger.info(f"提取了 {len(simplified_notes)} 個音符")
            
            return simplified_notes
        
        except ImportError:
            logger.error("librosa 未安裝")
            raise
        except Exception as e:
            logger.error(f"音頻分析錯誤: {str(e)}")
            raise
    
    def _midi_to_note(self, midi_note: int) -> str:
        """MIDI 編號轉 ABC 簡譜"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note = note_names[midi_note % 12]
        
        # 轉為簡譜數字
        if note in ['C', 'D', 'E', 'F', 'G', 'A', 'B']:
            note_map = {'C': '1', 'D': '2', 'E': '3', 'F': '4', 'G': '5', 'A': '6', 'B': '7'}
            return note_map[note]
        return '5'  # 升降記號統一為 5
    
    def _simplify_notes(self, notes: List, min_frames: int = 5) -> List[Dict]:
        """簡化音符序列"""
        if not notes:
            return []
        
        simplified = []
        current_note = None
        count = 0
        
        for note in notes:
            if note is None:
                if current_note and count >= min_frames:
                    simplified.append(current_note)
                current_note = None
                count = 0
            elif current_note is None:
                current_note = note
                count = 1
            elif note['note'] == current_note['note']:
                count += 1
            else:
                if count >= min_frames:
                    simplified.append(current_note)
                current_note = note
                count = 1
        
        if current_note and count >= min_frames:
            simplified.append(current_note)
        
        return simplified
    
    def generate_jianpu(self, notes: List[Dict], difficulty: str = "normal") -> Dict:
        """生成簡譜"""
        try:
            logger.info(f"生成簡譜 - 難度: {difficulty}, 音符數: {len(notes)}")
            
            if not notes:
                notes_str = "1 2 3 4 5 6 7 1' -"
            else:
                # 提取音符序列
                note_sequence = [note['note'] for note in notes if note]
                
                # 根據難度調整
                if difficulty == "easy":
                    # 簡化版本：每隔 2-3 個取 1 個
                    note_sequence = note_sequence[::3]
                elif difficulty == "hard":
                    # 完整版本
                    pass
                else:  # normal
                    # 每隔 1-2 個取 1 個
                    note_sequence = note_sequence[::2]
                
                notes_str = " ".join(note_sequence)
            
            # 簡譜資料結構
            jianpu = {
                "notes": notes_str,
                "fingering": f"{difficulty} 難度運指",
                "tempo": 80 if difficulty == "easy" else (120 if difficulty == "normal" else 140),
                "key": "C",
                "time_signature": "4/4"
            }
            
            logger.info(f"簡譜生成完成: {jianpu}")
            return jianpu
        
        except Exception as e:
            logger.error(f"簡譜生成錯誤: {str(e)}")
            raise
    
    def generate_midi(self, notes: List[Dict], title: str, difficulty: str = "normal") -> Optional[str]:
        """生成 MIDI 文件"""
        try:
            logger.info(f"生成 MIDI 文件 - {title}")
            
            try:
                from midiutil import MIDIFile
            except ImportError:
                logger.warning("midiutil 未安裝，跳過 MIDI 生成")
                return None
            
            # 創建 MIDI 文件
            midi = MIDIFile(1)  # 單聲道
            track = 0
            channel = 0
            time = 0
            volume = 100
            
            # 根據難度調整速度
            if difficulty == "easy":
                tempo = 80
            elif difficulty == "hard":
                tempo = 140
            else:
                tempo = 120
            
            midi.addTempo(track, 0, tempo)
            
            # 添加音符
            duration = 1  # 每個音符 1 拍
            
            if not notes:
                # 示例 MIDI
                note_sequence = [60, 62, 64, 65, 67, 69, 71, 72]
            else:
                note_sequence = [note['midi'] for note in notes if note and 'midi' in note]
            
            for pitch in note_sequence:
                midi.addNote(track, channel, pitch, time, duration, volume)
                time += duration
            
            # 儲存 MIDI 文件
            output_path = self.data_dir / f"{title}_{difficulty}.mid"
            with open(output_path, 'wb') as output_file:
                midi.writeFile(output_file)
            
            logger.info(f"MIDI 文件已保存: {output_path}")
            return str(output_path)
        
        except Exception as e:
            logger.error(f"MIDI 生成錯誤: {str(e)}")
            return None


# 全域實例
task_manager = TaskManager()
audio_processor = AudioProcessor()
