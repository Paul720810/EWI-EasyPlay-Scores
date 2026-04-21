"""
EWI EasyPlay - YouTube 集成
從 YouTube 視頻下載和提取音訊
"""

import logging
import os
import subprocess
from typing import Optional, Dict, Tuple
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class YouTubeIntegration:
    """YouTube 數據源集成"""

    def __init__(self, download_dir: Optional[str] = None):
        """
        初始化 YouTube 集成

        Args:
            download_dir: 下載目錄 (預設為臨時目錄)
        """
        self.download_dir = download_dir or tempfile.gettempdir()
        self._verify_dependencies()
        logger.info(f"初始化 YouTubeIntegration (下載目錄: {self.download_dir})")

    def _verify_dependencies(self):
        """驗證必要的依賴"""
        try:
            # 檢查 yt-dlp
            result = subprocess.run(['yt-dlp', '--version'],
                                   capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("yt-dlp 未安裝或不可用")
                return False

            logger.debug(f"yt-dlp 版本: {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            logger.warning("yt-dlp 未安裝")
            return False

    def validate_url(self, url: str) -> bool:
        """
        驗證 YouTube URL

        Args:
            url: YouTube URL

        Returns:
            valid: URL 是否有效
        """
        valid_hosts = ['youtube.com', 'youtu.be', 'www.youtube.com']
        return any(host in url for host in valid_hosts)

    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        獲取 YouTube 視頻信息

        Args:
            url: YouTube URL

        Returns:
            info: 視頻信息字典
        """
        try:
            if not self.validate_url(url):
                logger.error(f"無效的 YouTube URL: {url}")
                return None

            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                '-j',
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"無法獲取視頻信息: {result.stderr}")
                return None

            import json
            info = json.loads(result.stdout)

            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'url': url,
                'id': info.get('id', ''),
                'description': info.get('description', '')
            }

        except Exception as e:
            logger.error(f"獲取視頻信息失敗: {e}")
            return None

    def download_audio(
        self,
        url: str,
        output_path: Optional[str] = None,
        audio_format: str = 'wav'
    ) -> Optional[str]:
        """
        從 YouTube 視頻下載音訊

        Args:
            url: YouTube URL
            output_path: 輸出文件路徑
            audio_format: 音訊格式 (mp3, wav, m4a)

        Returns:
            path: 下載的音訊文件路徑
        """
        try:
            if not self.validate_url(url):
                logger.error(f"無效的 YouTube URL: {url}")
                return None

            # 獲取視頻信息
            info = self.get_video_info(url)
            if not info:
                return None

            # 生成輸出文件名
            if output_path is None:
                safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_'))[:50]
                output_path = os.path.join(self.download_dir, f"{safe_title}.{audio_format}")

            # 確保目錄存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 構建 yt-dlp 命令
            cmd = [
                'yt-dlp',
                '-x',  # 提取音訊
                '--audio-format', audio_format,
                '--audio-quality', '192',
                '-o', output_path,
                '--no-warnings',
                url
            ]

            logger.info(f"下載 {info['title']} 的音訊...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"下載失敗: {result.stderr}")
                return None

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                logger.info(f"音訊下載完成: {output_path} ({file_size:.2f} MB)")
                return output_path
            else:
                logger.error("下載文件不存在")
                return None

        except subprocess.TimeoutExpired:
            logger.error("下載超時")
            return None
        except Exception as e:
            logger.error(f"下載音訊失敗: {e}")
            return None

    def get_download_status(self, url: str) -> Dict:
        """
        獲取下載狀態

        Args:
            url: YouTube URL

        Returns:
            status: 狀態信息
        """
        try:
            info = self.get_video_info(url)
            if not info:
                return {'status': 'error', 'message': '無法獲取視頻信息'}

            return {
                'status': 'ready',
                'title': info['title'],
                'duration': info['duration'],
                'uploader': info['uploader'],
                'message': f"已準備好下載: {info['title']}"
            }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}
