"""
EWI EasyPlay - Spotify 集成
從 Spotify 下載和播放歌曲
"""

import logging
import os
from typing import Optional, Dict, List
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SpotifyIntegration:
    """Spotify 數據源集成"""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = 'http://localhost:8888/callback'
    ):
        """
        初始化 Spotify 集成

        Args:
            client_id: Spotify 應用 ID
            client_secret: Spotify 應用密鑰
            redirect_uri: 重定向 URI
        """
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = redirect_uri
        self.authenticated = False
        self.access_token = None

        logger.info("初始化 SpotifyIntegration")

        # 嘗試導入 spotipy
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            self.spotipy = spotipy
            self.SpotifyClientCredentials = SpotifyClientCredentials
        except ImportError:
            logger.warning("Spotipy 未安裝")
            self.spotipy = None

    def authenticate(self) -> bool:
        """
        使用客戶端認證進行 Spotify 認證

        Returns:
            success: 認證是否成功
        """
        try:
            if not self.spotipy:
                logger.error("Spotipy 未安裝")
                return False

            if not self.client_id or not self.client_secret:
                logger.error("缺少 Spotify 認證信息")
                return False

            auth_manager = self.SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            self.sp = self.spotipy.Spotify(auth_manager=auth_manager)
            self.authenticated = True

            logger.info("Spotify 認證成功")
            return True

        except Exception as e:
            logger.error(f"Spotify 認證失敗: {e}")
            return False

    def search_track(self, query: str, limit: int = 10) -> List[Dict]:
        """
        在 Spotify 中搜索曲目

        Args:
            query: 搜索查詢 (歌曲名或藝術家名)
            limit: 結果限制

        Returns:
            results: 曲目列表
        """
        try:
            if not self.authenticated:
                if not self.authenticate():
                    return []

            results = self.sp.search(q=query, type='track', limit=limit)

            tracks = []
            for track in results['tracks']['items']:
                tracks.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([a['name'] for a in track['artists']]),
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'preview_url': track.get('preview_url'),
                    'popularity': track.get('popularity', 0)
                })

            logger.info(f"找到 {len(tracks)} 個 Spotify 曲目")
            return tracks

        except Exception as e:
            logger.error(f"搜索失敗: {e}")
            return []

    def get_track_info(self, track_id: str) -> Optional[Dict]:
        """
        獲取曲目詳細信息

        Args:
            track_id: Spotify 曲目 ID

        Returns:
            info: 曲目信息
        """
        try:
            if not self.authenticated:
                if not self.authenticate():
                    return None

            track = self.sp.track(track_id)

            return {
                'id': track['id'],
                'name': track['name'],
                'artist': ', '.join([a['name'] for a in track['artists']]),
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'release_date': track['album'].get('release_date'),
                'popularity': track.get('popularity'),
                'preview_url': track.get('preview_url'),
                'external_urls': track.get('external_urls', {})
            }

        except Exception as e:
            logger.error(f"無法獲取曲目信息: {e}")
            return None

    def get_audio_features(self, track_id: str) -> Optional[Dict]:
        """
        獲取曲目的音訊特徵

        Args:
            track_id: Spotify 曲目 ID

        Returns:
            features: 音訊特徵 (BPM, Key, Time Signature 等)
        """
        try:
            if not self.authenticated:
                if not self.authenticate():
                    return None

            features = self.sp.audio_features(track_id)[0]

            return {
                'tempo': features.get('tempo'),  # BPM
                'key': features.get('key'),  # 0-11 (C to B)
                'mode': features.get('mode'),  # 0 = minor, 1 = major
                'time_signature': features.get('time_signature'),
                'energy': features.get('energy'),  # 0-1
                'danceability': features.get('danceability'),  # 0-1
                'valence': features.get('valence'),  # 0-1 (positivity)
                'acousticness': features.get('acousticness'),  # 0-1
                'instrumentalness': features.get('instrumentalness'),  # 0-1
                'liveness': features.get('liveness'),  # 0-1
                'speechiness': features.get('speechiness'),  # 0-1
                'loudness': features.get('loudness')  # dB
            }

        except Exception as e:
            logger.error(f"無法獲取音訊特徵: {e}")
            return None

    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> List[Dict]:
        """
        獲取播放列表中的曲目

        Args:
            playlist_id: Spotify 播放列表 ID
            limit: 限制數量

        Returns:
            tracks: 曲目列表
        """
        try:
            if not self.authenticated:
                if not self.authenticate():
                    return []

            results = self.sp.playlist_tracks(playlist_id, limit=limit)

            tracks = []
            for item in results['items']:
                track = item['track']
                if track:
                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join([a['name'] for a in track['artists']]),
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'preview_url': track.get('preview_url')
                    })

            logger.info(f"獲取 {len(tracks)} 個播放列表曲目")
            return tracks

        except Exception as e:
            logger.error(f"無法獲取播放列表: {e}")
            return []

    def export_playlist(self, playlist_id: str, output_file: str) -> bool:
        """
        匯出播放列表為 JSON

        Args:
            playlist_id: Spotify 播放列表 ID
            output_file: 輸出文件路徑

        Returns:
            success: 是否成功
        """
        try:
            tracks = self.get_playlist_tracks(playlist_id, limit=100)

            playlist_data = {
                'playlist_id': playlist_id,
                'track_count': len(tracks),
                'tracks': tracks
            }

            Path(output_file).parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, ensure_ascii=False, indent=2)

            logger.info(f"播放列表已匯出: {output_file}")
            return True

        except Exception as e:
            logger.error(f"匯出播放列表失敗: {e}")
            return False

    def get_recommendations(
        self,
        seed_tracks: List[str] = None,
        seed_artists: List[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        基於種子獲取推薦曲目

        Args:
            seed_tracks: 種子曲目 ID 列表
            seed_artists: 種子藝術家 ID 列表
            limit: 限制數量

        Returns:
            tracks: 推薦曲目列表
        """
        try:
            if not self.authenticated:
                if not self.authenticate():
                    return []

            recommendations = self.sp.recommendations(
                seed_tracks=seed_tracks or [],
                seed_artists=seed_artists or [],
                limit=limit
            )

            tracks = []
            for track in recommendations['tracks']:
                tracks.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([a['name'] for a in track['artists']]),
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms']
                })

            logger.info(f"獲取 {len(tracks)} 個推薦曲目")
            return tracks

        except Exception as e:
            logger.error(f"無法獲取推薦: {e}")
            return []
