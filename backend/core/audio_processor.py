"""
音訊分析與處理模塊

功能：
- 加載多格式音訊（MP3、WAV、FLAC 等）
- 特徵提取（MFCC、Chroma、Spectral Centroid）
- 預處理管道（降噪、正規化、分段）

Author: EWI Development Team
License: MIT
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, List, Optional

import librosa
import numpy as np

try:
    import soundfile as sf
except ImportError:  # pragma: no cover - fallback only used when available
    sf = None

try:
    from scipy.signal import resample_poly
except ImportError:  # pragma: no cover - scipy is part of the normal runtime
    resample_poly = None

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    音訊處理引擎

    提供音訊加載、特徵提取、預處理等功能
    """

    def __init__(self, sr: int = 22050, n_mfcc: int = 13):
        """
        初始化音訊處理器

        Args:
            sr (int): 采樣率，默認 22050 Hz
            n_mfcc (int): MFCC 係數數量，默認 13
        """
        self.sr = sr
        self.n_mfcc = n_mfcc
        self.logger = logger

    def load_audio(self, file_path: str, duration: Optional[float] = None,
                   offset: float = 0.0) -> Tuple[np.ndarray, int]:
        """
        加載音訊文件

        Args:
            file_path (str): 音訊文件路徑
            duration (float): 最大加載時長（秒），None 表示加載全部
            offset (float): 開始時間偏移（秒）

        Returns:
            Tuple[np.ndarray, int]: (音訊數據, 采樣率)

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"音訊文件不存在: {file_path}")

            y, sr = self._load_audio_with_fallback(file_path, duration=duration, offset=offset)

            self.logger.info(
                f"✅ 加載音訊: {file_path}\n"
                f"   采樣率: {sr} Hz\n"
                f"   時長: {len(y)/sr:.2f}s\n"
                f"   幀數: {len(y)}"
            )
            return y, sr
        except Exception as e:
            self.logger.error(f"❌ 加載失敗: {e}")
            raise

    def _load_audio_with_fallback(self, file_path: str, duration: Optional[float] = None,
                                  offset: float = 0.0) -> Tuple[np.ndarray, int]:
        """優先使用 librosa，失敗時改用 soundfile 直接讀取。"""
        try:
            return librosa.load(file_path, sr=self.sr, duration=duration, offset=offset)
        except ModuleNotFoundError:
            if sf is None:
                raise

            y, sr = sf.read(file_path, always_2d=False)

            if y.ndim > 1:
                y = np.mean(y, axis=1)

            start_sample = int(offset * sr)
            if start_sample > 0:
                y = y[start_sample:]

            if duration is not None:
                end_sample = start_sample + int(duration * sr)
                y = y[:max(0, end_sample - start_sample)]

            y = np.asarray(y, dtype=np.float32)

            if sr != self.sr:
                if resample_poly is None:
                    raise ModuleNotFoundError("scipy.signal.resample_poly 無法使用")

                gcd = np.gcd(sr, self.sr)
                y = resample_poly(y, self.sr // gcd, sr // gcd).astype(np.float32)
                sr = self.sr

            return y, sr

    def extract_features(self, y: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """
        提取音訊特徵

        Args:
            y (np.ndarray): 音訊數據
            sr (int): 采樣率

        Returns:
            Dict: 包含各種特徵的字典
                - mfcc: MFCC 特徵 (n_mfcc, n_frames)
                - chroma: Chroma 特徵 (12, n_frames)
                - spectral_centroid: 色譜質心 (1, n_frames)
                - spectral_rolloff: 色譜滾降 (1, n_frames)
                - zcr: 零交叉率 (1, n_frames)
                - rms_energy: RMS 能量 (1, n_frames)
        """
        try:
            features = {}

            # 提取 MFCC（梅爾頻率倒譜係數）
            # 最常用於音訊分類和特徵提取
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
            features['mfcc'] = mfcc

            # 提取 Chroma 特徵（色度特徵）
            # 表示 12 個音級類的能量分佈
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            features['chroma'] = chroma

            # 提取色譜質心
            # 表示音訊頻譜的"質心"
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            features['spectral_centroid'] = spectral_centroid

            # 提取色譜滾降
            # 頻率以下 85% 能量集中的點
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            features['spectral_rolloff'] = spectral_rolloff

            # 提取零交叉率
            # 音訊信號改變符號的頻率
            zcr = librosa.feature.zero_crossing_rate(y)
            features['zcr'] = zcr

            # 提取 RMS 能量
            # 音訊的整體音量
            rms_energy = librosa.feature.rms(y=y)
            features['rms_energy'] = rms_energy

            # 補齊摘要統計，供上層任務與整合測試直接使用
            features['mfcc_mean'] = np.mean(mfcc, axis=1)
            features['mfcc_std'] = np.std(mfcc, axis=1)
            features['chroma_mean'] = np.mean(chroma, axis=1)
            features['chroma_std'] = np.std(chroma, axis=1)
            features['spectral_mean'] = np.mean(spectral_centroid, axis=1)
            features['spectral_std'] = np.std(spectral_centroid, axis=1)
            features['spectral_centroid_mean'] = features['spectral_mean']
            features['spectral_centroid_std'] = features['spectral_std']
            features['rolloff_mean'] = np.mean(spectral_rolloff, axis=1)
            features['rolloff_std'] = np.std(spectral_rolloff, axis=1)
            features['zcr_mean'] = np.mean(zcr, axis=1)
            features['zcr_std'] = np.std(zcr, axis=1)
            features['rms_mean'] = np.mean(rms_energy, axis=1)
            features['rms_std'] = np.std(rms_energy, axis=1)

            self.logger.info(
                f"✅ 特徵提取完成\n"
                f"   MFCC 形狀: {mfcc.shape}\n"
                f"   Chroma 形狀: {chroma.shape}\n"
                f"   時間幀數: {mfcc.shape[1]}"
            )
            return features
        except Exception as e:
            self.logger.error(f"❌ 特徵提取失敗: {e}")
            raise

    def normalize_audio(self, y: np.ndarray, method: str = 'peak') -> np.ndarray:
        """
        正規化音訊（防止失真和標準化）

        Args:
            y (np.ndarray): 音訊數據
            method (str): 正規化方法
                - 'peak': 峰值正規化到 ±1
                - 'rms': RMS 正規化到目標能量

        Returns:
            np.ndarray: 正規化後的音訊
        """
        if method == 'peak':
            max_val = np.max(np.abs(y))
            if max_val > 0:
                return y / max_val
            return y
        elif method == 'rms':
            rms = np.sqrt(np.mean(y**2))
            if rms > 0:
                # 目標 RMS 為 0.1
                return y * (0.1 / rms)
            return y
        else:
            raise ValueError(f"未知的正規化方法: {method}")

    def segment_audio(self, y: np.ndarray, sr: int,
                      segment_duration: float = 2.0,
                      hop_duration: Optional[float] = None) -> List[np.ndarray]:
        """
        將音訊分段處理（滑動窗口）

        Args:
            y (np.ndarray): 音訊數據
            sr (int): 采樣率
            segment_duration (float): 每段時長（秒）
            hop_duration (float): 滑動間隔（秒），默認等於 segment_duration（非重疊）

        Returns:
            List[np.ndarray]: 分段後的音訊列表
        """
        segment_samples = int(segment_duration * sr)
        hop_samples = int((hop_duration or segment_duration) * sr)

        segments = []

        for i in range(0, len(y) - segment_samples + 1, hop_samples):
            segment = y[i:i+segment_samples]
            if len(segment) == segment_samples:  # 確保完整段
                segments.append(segment)

        # 處理最後不完整的段
        if len(y) % hop_samples > segment_samples // 2:
            last_segment = y[-segment_samples:]
            if len(last_segment) == segment_samples:
                segments.append(last_segment)

        self.logger.info(
            f"✅ 音訊分段完成\n"
            f"   總段數: {len(segments)}\n"
            f"   每段時長: {segment_duration}s\n"
            f"   滑動間隔: {hop_duration or segment_duration}s"
        )
        return segments

    def get_tempo_and_beats(self, y: np.ndarray, sr: int) -> Tuple[float, np.ndarray]:
        """
        估計音訊的節奏和節拍

        Args:
            y (np.ndarray): 音訊數據
            sr (int): 采樣率

        Returns:
            Tuple[float, np.ndarray]: (BPM, 節拍幀位置)
        """
        try:
            # 計算始終圖
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)

            # 估計節奏
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

            self.logger.info(
                f"✅ 節奏估計完成\n"
                f"   BPM: {tempo:.2f}\n"
                f"   檢測到的節拍數: {len(beats)}"
            )
            return tempo, beats
        except Exception as e:
            self.logger.error(f"❌ 節奏估計失敗: {e}")
            raise

    def process_pipeline(self, file_path: str, duration: Optional[float] = None,
                        normalize: bool = True) -> Dict:
        """
        完整的音訊處理管道

        Args:
            file_path (str): 音訊文件路徑
            duration (float): 加載時長限制
            normalize (bool): 是否進行正規化

        Returns:
            Dict: 包含加載的音訊和提取的特徵
        """
        # 加載音訊
        y, sr = self.load_audio(file_path, duration=duration)

        # 正規化
        if normalize:
            y = self.normalize_audio(y)

        # 提取特徵
        features = self.extract_features(y, sr)

        # 估計節奏
        tempo, beats = self.get_tempo_and_beats(y, sr)

        return {
            'audio': y,
            'sr': sr,
            'duration': len(y) / sr,
            'features': features,
            'tempo': tempo,
            'beats': beats
        }
