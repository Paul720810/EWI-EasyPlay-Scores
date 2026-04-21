"""
音訊處理器單元測試

測試 AudioProcessor 的主要功能
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import soundfile as sf

from core.audio_processor import AudioProcessor


class TestAudioProcessor:
    """測試 AudioProcessor 類"""

    @pytest.fixture
    def processor(self):
        """建立 AudioProcessor 實例"""
        return AudioProcessor(sr=22050, n_mfcc=13)

    @pytest.fixture
    def test_audio_file(self):
        """建立測試音訊文件"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            # 生成 2 秒的測試信號（440 Hz 正弦波）
            sr = 22050
            duration = 2.0
            t = np.linspace(0, duration, int(sr * duration))
            frequency = 440  # A4 音符
            y = 0.3 * np.sin(2 * np.pi * frequency * t)

            # 保存為 WAV 文件
            sf.write(tmp.name, y, sr)
            yield tmp.name

            # 清理
            Path(tmp.name).unlink()

    def test_load_audio(self, processor, test_audio_file):
        """測試音訊加載"""
        y, sr = processor.load_audio(test_audio_file)

        assert isinstance(y, np.ndarray)
        assert sr == 22050
        assert len(y) > 0

    def test_load_audio_with_duration(self, processor, test_audio_file):
        """測試帶時長限制的音訊加載"""
        y, sr = processor.load_audio(test_audio_file, duration=1.0)

        # 應該只加載 ~1 秒
        assert len(y) / sr <= 1.1  # 允許 10% 誤差

    def test_normalize_audio_peak(self, processor):
        """測試峰值正規化"""
        test_audio = np.array([0.5, -0.8, 1.2, -1.5])
        normalized = processor.normalize_audio(test_audio, method='peak')

        # 檢查最大絕對值
        assert np.max(np.abs(normalized)) == pytest.approx(1.0, abs=1e-6)

    def test_normalize_audio_rms(self, processor):
        """測試 RMS 正規化"""
        test_audio = np.array([0.5, -0.8, 1.2, -1.5] * 1000)
        normalized = processor.normalize_audio(test_audio, method='rms')

        # 計算 RMS
        rms = np.sqrt(np.mean(normalized ** 2))
        assert rms == pytest.approx(0.1, abs=0.01)

    def test_segment_audio(self, processor):
        """測試音訊分段"""
        # 建立 4 秒的測試音訊
        sr = 22050
        duration = 4
        test_audio = np.random.randn(sr * duration)

        segments = processor.segment_audio(test_audio, sr, segment_duration=2.0)

        # 應該分為 2 段
        assert len(segments) >= 2
        # 每段應該是 2 秒
        for segment in segments[:2]:
            assert len(segment) == sr * 2

    def test_extract_features(self, processor, test_audio_file):
        """測試特徵提取"""
        y, sr = processor.load_audio(test_audio_file)
        features = processor.extract_features(y, sr)

        # 檢查必要的特徵
        assert 'mfcc' in features
        assert 'chroma' in features
        assert 'spectral_centroid' in features
        assert 'spectral_rolloff' in features
        assert 'zcr' in features
        assert 'rms_energy' in features

        # 檢查形狀
        assert features['mfcc'].shape[0] == 13  # n_mfcc
        assert features['chroma'].shape[0] == 12  # 12 個音級

    def test_get_tempo_and_beats(self, processor, test_audio_file):
        """測試節奏估計"""
        y, sr = processor.load_audio(test_audio_file)
        tempo, beats = processor.get_tempo_and_beats(y, sr)

        # 檢查返回值類型
        assert isinstance(tempo, (int, float))
        assert isinstance(beats, np.ndarray)

        # BPM 應該在合理範圍內
        assert 30 < tempo < 300

    def test_process_pipeline(self, processor, test_audio_file):
        """測試完整的處理管道"""
        result = processor.process_pipeline(test_audio_file)

        # 檢查必要的鍵
        assert 'audio' in result
        assert 'sr' in result
        assert 'duration' in result
        assert 'features' in result
        assert 'tempo' in result
        assert 'beats' in result

        # 檢查值
        assert result['sr'] == 22050
        assert result['duration'] > 0
        assert isinstance(result['features'], dict)
        assert result['tempo'] > 0

    def test_load_nonexistent_file(self, processor):
        """測試加載不存在的文件"""
        with pytest.raises(FileNotFoundError):
            processor.load_audio('/nonexistent/file.wav')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
