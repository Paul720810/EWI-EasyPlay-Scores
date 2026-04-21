"""
EWI EasyPlay - 前端服務層
負責前端 API 通信和數據管理
"""

import logging
from typing import Optional, Dict, List, BinaryIO
import aiofiles
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class FileService:
    """文件上傳和管理服務"""

    def __init__(self, upload_dir: str = '/tmp/uploads'):
        """
        初始化文件服務

        Args:
            upload_dir: 上傳目錄
        """
        self.upload_dir = upload_dir
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"初始化文件服務 (目錄: {upload_dir})")

    async def upload_audio(self, file: BinaryIO, filename: str) -> Dict:
        """
        上傳音訊文件

        Args:
            file: 文件對象
            filename: 文件名

        Returns:
            result: 上傳結果
        """
        try:
            file_path = Path(self.upload_dir) / filename

            # 讀取並保存文件
            content = await file.read()

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            file_size = len(content) / (1024 * 1024)  # MB

            logger.info(f"音訊文件已上傳: {filename} ({file_size:.2f} MB)")

            return {
                'status': 'success',
                'filename': filename,
                'path': str(file_path),
                'size_mb': round(file_size, 2),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"文件上傳失敗: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    async def delete_file(self, filename: str) -> Dict:
        """
        刪除已上傳的文件

        Args:
            filename: 文件名

        Returns:
            result: 刪除結果
        """
        try:
            file_path = Path(self.upload_dir) / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"文件已刪除: {filename}")
                return {'status': 'success', 'message': f'{filename} 已刪除'}
            else:
                return {'status': 'failed', 'error': '文件不存在'}

        except Exception as e:
            logger.error(f"文件刪除失敗: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def list_files(self) -> List[Dict]:
        """
        列出所有已上傳的文件

        Returns:
            files: 文件列表
        """
        try:
            files = []
            for file_path in Path(self.upload_dir).glob('*'):
                if file_path.is_file():
                    files.append({
                        'filename': file_path.name,
                        'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
                        'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                        'path': str(file_path)
                    })

            return files

        except Exception as e:
            logger.error(f"列出文件失敗: {e}")
            return []


class ProcessingService:
    """音樂處理服務"""

    @staticmethod
    async def start_processing(file_path: str, processing_type: str = 'full') -> Dict:
        """
        開始處理音樂文件

        Args:
            file_path: 文件路徑
            processing_type: 處理類型 ('full', 'pitch_only', 'difficulty_only')

        Returns:
            result: 任務信息
        """
        try:
            from services.task_queue import (
                process_music_pipeline,
                detect_pitch_task,
                grade_difficulty_task
            )

            logger.info(f"開始音樂處理: {file_path} (類型: {processing_type})")

            if processing_type == 'full':
                # 完整管道
                task = process_music_pipeline.apply_async(
                    args=[file_path],
                    kwargs={'output_dir': '/tmp/outputs'}
                )
            elif processing_type == 'pitch_only':
                # 僅音高檢測
                task = detect_pitch_task.apply_async(args=[file_path])
            else:
                return {'status': 'failed', 'error': '未知的處理類型'}

            return {
                'status': 'started',
                'task_id': task.id,
                'processing_type': processing_type,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"處理啟動失敗: {e}")
            return {'status': 'failed', 'error': str(e)}

    @staticmethod
    async def get_processing_status(task_id: str) -> Dict:
        """
        獲取處理狀態

        Args:
            task_id: 任務 ID

        Returns:
            status: 狀態信息
        """
        try:
            from services.task_queue import TaskManager

            return TaskManager.get_task_status(task_id)

        except Exception as e:
            logger.error(f"獲取狀態失敗: {e}")
            return {'status': 'failed', 'error': str(e)}


class DataSourceService:
    """數據源服務 (YouTube, Spotify)"""

    @staticmethod
    async def search_youtube(query: str) -> List[Dict]:
        """
        搜索 YouTube

        Args:
            query: 搜索查詢

        Returns:
            results: 搜索結果
        """
        try:
            from integrations.youtube_integration import YouTubeIntegration

            yt = YouTubeIntegration()
            # 實現搜索邏輯
            logger.info(f"搜索 YouTube: {query}")
            return []

        except Exception as e:
            logger.error(f"YouTube 搜索失敗: {e}")
            return []

    @staticmethod
    async def search_spotify(query: str) -> List[Dict]:
        """
        搜索 Spotify

        Args:
            query: 搜索查詢

        Returns:
            results: 搜索結果
        """
        try:
            from integrations.spotify_integration import SpotifyIntegration

            spotify = SpotifyIntegration()
            results = spotify.search_track(query, limit=10)

            logger.info(f"搜索 Spotify: {query} (找到 {len(results)} 個結果)")
            return results

        except Exception as e:
            logger.error(f"Spotify 搜索失敗: {e}")
            return []

    @staticmethod
    async def download_from_url(url: str, source_type: str = 'youtube') -> Dict:
        """
        從 URL 下載音樂

        Args:
            url: 音樂 URL
            source_type: 源類型 ('youtube', 'spotify')

        Returns:
            result: 下載結果
        """
        try:
            if source_type == 'youtube':
                from integrations.youtube_integration import YouTubeIntegration
                yt = YouTubeIntegration(download_dir='/tmp/downloads')
                file_path = yt.download_audio(url)

                if file_path:
                    return {
                        'status': 'success',
                        'file_path': file_path,
                        'source': 'youtube'
                    }
                else:
                    return {'status': 'failed', 'error': 'YouTube 下載失敗'}

            else:
                return {'status': 'failed', 'error': '不支持的源類型'}

        except Exception as e:
            logger.error(f"下載失敗: {e}")
            return {'status': 'failed', 'error': str(e)}


class AnalyticsService:
    """分析和統計服務"""

    @staticmethod
    def get_user_statistics(user_id: str) -> Dict:
        """
        獲取用戶統計信息

        Args:
            user_id: 用戶 ID

        Returns:
            stats: 統計信息
        """
        return {
            'user_id': user_id,
            'songs_processed': 0,
            'total_playtime': 0,
            'favorite_difficulty': 'normal',
            'last_activity': datetime.now().isoformat()
        }

    @staticmethod
    def get_leaderboard(limit: int = 10) -> List[Dict]:
        """
        獲取排行榜

        Args:
            limit: 限制數量

        Returns:
            leaderboard: 排行榜數據
        """
        return [
            {
                'rank': i + 1,
                'username': f'User{i}',
                'score': 1000 - (i * 100),
                'level': 'Advanced'
            }
            for i in range(min(limit, 10))
        ]


class UserPreferenceService:
    """用戶偏好設置服務"""

    def __init__(self, data_dir: str = '/tmp/preferences'):
        """
        初始化用戶偏好服務

        Args:
            data_dir: 數據目錄
        """
        self.data_dir = data_dir
        Path(data_dir).mkdir(parents=True, exist_ok=True)

    async def save_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """
        保存用戶偏好

        Args:
            user_id: 用戶 ID
            preferences: 偏好設置

        Returns:
            result: 保存結果
        """
        try:
            pref_file = Path(self.data_dir) / f"{user_id}_prefs.json"

            async with aiofiles.open(pref_file, 'w') as f:
                await f.write(json.dumps(preferences, indent=2))

            logger.info(f"用戶偏好已保存: {user_id}")
            return {'status': 'success', 'message': '偏好已保存'}

        except Exception as e:
            logger.error(f"保存偏好失敗: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def get_preferences(self, user_id: str) -> Dict:
        """
        獲取用戶偏好

        Args:
            user_id: 用戶 ID

        Returns:
            preferences: 用戶偏好
        """
        try:
            pref_file = Path(self.data_dir) / f"{user_id}_prefs.json"

            if pref_file.exists():
                async with aiofiles.open(pref_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            else:
                # 返回默認偏好
                return {
                    'difficulty': 'normal',
                    'language': 'zh-TW',
                    'notifications': True,
                    'dark_mode': False
                }

        except Exception as e:
            logger.error(f"獲取偏好失敗: {e}")
            return {}
