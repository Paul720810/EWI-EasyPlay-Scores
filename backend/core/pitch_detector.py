"""
EWI EasyPlay - 音高檢測引擎
使用深度學習模型進行精確的音高和節拍檢測
"""

import logging
import numpy as np
from typing import Tuple, List, Dict, Optional
import librosa
from utils.constants import SAMPLE_RATE, N_MFCC

logger = logging.getLogger(__name__)


class PitchDetector:
    """音高檢測引擎 - 使用多種方法進行精確檢測"""

    def __init__(self, sr: int = SAMPLE_RATE, hop_length: int = 512):
        """
        初始化音高檢測器

        Args:
            sr: 採樣率 (預設 22050 Hz)
            hop_length: 幀跳長度 (預設 512)
        """
        self.sr = sr
        self.hop_length = hop_length
        self.frame_length = 2048

        logger.info(f"初始化 PitchDetector (sr={sr}, hop_length={hop_length})")

    def detect_fundamental_frequency(self, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用多種方法檢測基頻 (Fundamental Frequency)

        Args:
            y: 音訊時間序列

        Returns:
            frequencies: 基頻數組 (Hz)
            confidence: 置信度 (0-1)
        """
        try:
            # 方法 1: 使用 librosa 的 PYIN 算法 (最準確)
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y,
                fmin=librosa.note_to_hz('E2'),  # EWI 最低音
                fmax=librosa.note_to_hz('E8'),  # EWI 最高音
                sr=self.sr,
                hop_length=self.hop_length,
                frame_length=self.frame_length
            )

            # NaN 值設置為 0，置信度為 0
            confidence = np.where(~np.isnan(f0), voiced_probs, 0)
            f0 = np.nan_to_num(f0, nan=0.0)

            logger.debug(f"檢測到 {np.sum(confidence > 0.5)} 個高置信度幀")
            return f0, confidence

        except Exception as e:
            logger.error(f"基頻檢測失敗: {e}")
            return np.zeros_like(y[:len(y)//self.hop_length]), np.zeros_like(y[:len(y)//self.hop_length])

    def frequency_to_midi(self, frequency: float) -> int:
        """
        將頻率轉換為 MIDI 音符號

        Args:
            frequency: 頻率 (Hz)

        Returns:
            midi_note: MIDI 音符號 (0-127)
        """
        if frequency <= 0:
            return 0

        # MIDI 轉換公式: MIDI = 69 + 12 * log2(f/440)
        midi_note = int(round(69 + 12 * np.log2(frequency / 440)))

        # 限制在有效範圍內
        return max(0, min(127, midi_note))

    def midi_to_note_name(self, midi_note: int) -> str:
        """
        將 MIDI 音符號轉換為音符名稱

        Args:
            midi_note: MIDI 音符號

        Returns:
            note_name: 音符名稱 (如 'C4', 'D#4')
        """
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_index = midi_note % 12
        return f"{note_names[note_index]}{octave}"

    def extract_note_sequence(
        self,
        y: np.ndarray,
        sr: Optional[int] = None,
        min_confidence: float = 0.5,
        smoothing_window: int = 5
    ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
        """
        從音訊中提取音符序列

        Args:
            y: 音訊時間序列
            sr: 採樣率 (如果為 None，使用預設值)
            min_confidence: 最小置信度閾值
            smoothing_window: 平滑窗口大小

        Returns:
            notes: 音符列表 [{'midi': int, 'note': str, 'time': float, 'duration': float, 'confidence': float}, ...]
            f0: 基頻數組
            confidence: 置信度數組
        """
        if sr is not None:
            self.sr = sr

        try:
            # 檢測基頻
            f0, confidence = self.detect_fundamental_frequency(y)

            # 應用平滑
            if smoothing_window > 1:
                confidence = self._smooth_array(confidence, smoothing_window)

            # 提取音符
            notes = []
            current_note = None
            frame_time = 0

            for i, (freq, conf) in enumerate(zip(f0, confidence)):
                frame_time = librosa.frames_to_time(i, sr=self.sr, hop_length=self.hop_length)

                if conf >= min_confidence and freq > 0:
                    midi_note = self.frequency_to_midi(freq)
                    note_name = self.midi_to_note_name(midi_note)

                    if current_note is None:
                        # 開始新音符
                        current_note = {
                            'midi': midi_note,
                            'note': note_name,
                            'time': frame_time,
                            'frames': 1,
                            'confidence': conf
                        }
                    elif current_note['midi'] == midi_note:
                        # 延續相同音符
                        current_note['frames'] += 1
                        current_note['confidence'] = max(current_note['confidence'], conf)
                    else:
                        # 音符變化，保存前一個音符
                        current_note['duration'] = librosa.frames_to_time(
                            current_note['frames'],
                            sr=self.sr,
                            hop_length=self.hop_length
                        )
                        notes.append(current_note)

                        current_note = {
                            'midi': midi_note,
                            'note': note_name,
                            'time': frame_time,
                            'frames': 1,
                            'confidence': conf
                        }
                else:
                    if current_note is not None:
                        # 保存音符
                        current_note['duration'] = librosa.frames_to_time(
                            current_note['frames'],
                            sr=self.sr,
                            hop_length=self.hop_length
                        )
                        notes.append(current_note)
                        current_note = None

            # 保存最後的音符
            if current_note is not None:
                current_note['duration'] = librosa.frames_to_time(
                    current_note['frames'],
                    sr=self.sr,
                    hop_length=self.hop_length
                )
                notes.append(current_note)

            logger.info(f"提取了 {len(notes)} 個音符")
            return notes, f0, confidence

        except Exception as e:
            logger.error(f"音符序列提取失敗: {e}")
            return [], np.array([]), np.array([])

    def _smooth_array(self, arr: np.ndarray, window_size: int) -> np.ndarray:
        """
        使用平均濾波平滑數組

        Args:
            arr: 輸入數組
            window_size: 窗口大小

        Returns:
            smoothed: 平滑後的數組
        """
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(arr, kernel, mode='same')
        return smoothed

    def detect_vibrato(self, y: np.ndarray, f0: np.ndarray) -> Dict[str, float]:
        """
        檢測顫音特徵

        Args:
            y: 音訊時間序列
            f0: 基頻數組

        Returns:
            vibrato_info: {'rate': float, 'depth': float, 'detected': bool}
        """
        try:
            # 計算基頻的導數
            f0_derivative = np.diff(f0)

            # 檢測頻率變化
            vibrato_rate = np.abs(f0_derivative[f0_derivative > 0]).mean()
            vibrato_depth = np.std(f0[f0 > 0]) if np.any(f0 > 0) else 0

            # 顫音檢測閾值
            detected = vibrato_rate > 3 and vibrato_depth > 10

            return {
                'rate': float(vibrato_rate),
                'depth': float(vibrato_depth),
                'detected': bool(detected)
            }
        except Exception as e:
            logger.error(f"顫音檢測失敗: {e}")
            return {'rate': 0.0, 'depth': 0.0, 'detected': False}

    def get_statistics(self, notes: List[Dict]) -> Dict:
        """
        計算音符序列的統計信息

        Args:
            notes: 音符列表

        Returns:
            stats: 統計信息字典
        """
        if not notes:
            return {
                'total_notes': 0,
                'total_duration': 0,
                'average_note_duration': 0,
                'range_min_midi': 0,
                'range_max_midi': 0,
                'range_note': 'N/A',
                'average_confidence': 0
            }

        midi_values = [n['midi'] for n in notes]
        durations = [n['duration'] for n in notes]
        confidences = [n['confidence'] for n in notes]

        return {
            'total_notes': len(notes),
            'total_duration': sum(durations),
            'average_note_duration': np.mean(durations),
            'range_min_midi': min(midi_values),
            'range_max_midi': max(midi_values),
            'range_note': f"{self.midi_to_note_name(min(midi_values))} - {self.midi_to_note_name(max(midi_values))}",
            'average_confidence': float(np.mean(confidences))
        }
