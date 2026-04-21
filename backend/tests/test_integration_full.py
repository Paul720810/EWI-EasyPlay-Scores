"""
EWI EasyPlay - Phase 7 整合測試
完整的端到端工作流測試
"""

import pytest
import tempfile
import os
import json
import asyncio
from pathlib import Path
import numpy as np

# 修正導入路徑
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.audio_processor import AudioProcessor
from core.pitch_detector import PitchDetector
from core.midi_generator import MIDIGenerator
from core.difficulty_engine import DifficultyEngine
from utils.constants import SAMPLE_RATE
from services.frontend_service import FileService, ProcessingService
from integrations.youtube_integration import YouTubeIntegration


class TestEnd2EndWorkflow:
    """端到端工作流測試"""

    @pytest.fixture
    def temp_dir(self):
        """創建臨時目錄"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def test_audio_file(self, temp_dir):
        """生成測試音訊文件"""
        try:
            import soundfile as sf
        except ImportError:
            pytest.skip("soundfile 未安裝")

        sr = SAMPLE_RATE
        duration = 2.0

        # 生成簡單的 C-D-E-F 序列
        t = np.linspace(0, duration, int(sr * duration))
        notes_freq = [262, 294, 330, 349]  # C, D, E, F

        y = np.zeros_like(t)
        for i, freq in enumerate(notes_freq):
            start = int(i * sr * duration / 4)
            end = int((i + 1) * sr * duration / 4)
            y[start:end] = 0.3 * np.sin(2 * np.pi * freq * t[start:end])

        file_path = os.path.join(temp_dir, 'test_audio.wav')
        sf.write(file_path, y, sr)

        return file_path

    def test_complete_processing_pipeline(self, test_audio_file, temp_dir):
        """測試完整處理管道"""

        # 步驟 1: 加載音訊
        processor = AudioProcessor(sr=SAMPLE_RATE)
        y, sr = processor.load_audio(test_audio_file)
        assert y is not None
        assert sr == SAMPLE_RATE

        # 步驟 2: 提取特徵
        features = processor.extract_features(y, sr)
        assert features is not None
        assert 'mfcc_mean' in features

        # 步驟 3: 提取音符
        detector = PitchDetector(sr=sr)
        notes, f0, confidence = detector.extract_note_sequence(y, sr, min_confidence=0.3)

        # 驗證音符
        assert len(notes) > 0
        for note in notes:
            assert 'midi' in note
            assert 'duration' in note
            assert note['midi'] > 0

        # 步驟 4: 生成 MIDI
        generator = MIDIGenerator()
        midi = generator.create_midi_file(notes)
        assert midi is not None

        # 步驟 5: 難度分級
        engine = DifficultyEngine()
        diff_set = engine.create_difficulty_set(notes)

        assert len(diff_set['easy']) > 0
        assert len(diff_set['normal']) > 0
        assert len(diff_set['hard']) > 0
        assert len(diff_set['easy']) <= len(diff_set['normal']) <= len(diff_set['hard'])

        # 步驟 6: 驗證統計信息
        stats = engine.get_statistics(notes)
        assert stats['total_notes'] > 0
        assert stats['difficulty_score'] >= 0

    def test_multi_format_support(self, temp_dir):
        """測試多格式支持"""
        try:
            import soundfile as sf
        except ImportError:
            pytest.skip("soundfile 未安裝")

        sr = SAMPLE_RATE
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        y = 0.3 * np.sin(2 * np.pi * 262 * t)

        # 測試多種格式
        formats = ['wav', 'flac']  # 'mp3' 可能需要 ffmpeg

        processor = AudioProcessor(sr=sr)

        for fmt in formats:
            file_path = os.path.join(temp_dir, f'test.{fmt}')
            sf.write(file_path, y, sr)

            y_loaded, sr_loaded = processor.load_audio(file_path)
            assert y_loaded is not None
            assert sr_loaded == sr

    def test_batch_processing(self, temp_dir):
        """測試批量處理"""
        try:
            import soundfile as sf
        except ImportError:
            pytest.skip("soundfile 未安裝")

        # 創建 5 個測試文件
        file_paths = []
        for i in range(5):
            sr = SAMPLE_RATE
            duration = 1.0
            t = np.linspace(0, duration, int(sr * duration))

            # 不同的頻率
            freq = 262 + (i * 10)
            y = 0.3 * np.sin(2 * np.pi * freq * t)

            file_path = os.path.join(temp_dir, f'test_{i}.wav')
            sf.write(file_path, y, sr)
            file_paths.append(file_path)

        # 批量處理
        processor = AudioProcessor()
        detector = PitchDetector()

        results = []
        for file_path in file_paths:
            y, sr = processor.load_audio(file_path)
            notes, _, _ = detector.extract_note_sequence(y, sr, min_confidence=0.3)
            results.append(len(notes))

        assert len(results) == 5
        assert all(count > 0 for count in results)


class TestErrorHandling:
    """錯誤處理測試"""

    def test_invalid_file_path(self):
        """測試無效文件路徑"""
        processor = AudioProcessor()
        with pytest.raises(FileNotFoundError):
            y, sr = processor.load_audio('/nonexistent/file.wav')

    def test_empty_notes_handling(self):
        """測試空音符列表處理"""
        generator = MIDIGenerator()
        midi = generator.create_midi_file([])
        assert midi is not None

        engine = DifficultyEngine()
        diff_set = engine.create_difficulty_set([])
        assert diff_set['easy'] == []
        assert diff_set['normal'] == []
        assert diff_set['hard'] == []

    def test_invalid_difficulty_level(self):
        """測試無效難度級別"""
        engine = DifficultyEngine()
        test_notes = [
            {'midi': 60, 'time': 0, 'duration': 0.5, 'confidence': 0.9}
        ]

        # 應該使用默認難度
        graded = engine.grade_notes(test_notes, 'invalid_level')
        assert len(graded) > 0


class TestPerformance:
    """性能測試"""

    def test_large_note_sequence(self):
        """測試大型音符序列處理"""
        # 生成 1000 個音符
        notes = [
            {
                'midi': 60 + (i % 12),
                'time': i * 0.1,
                'duration': 0.08,
                'confidence': 0.9
            }
            for i in range(1000)
        ]

        # 難度分級
        engine = DifficultyEngine()
        diff_set = engine.create_difficulty_set(notes)

        assert len(diff_set['easy']) > 0
        assert len(diff_set['normal']) > 0
        assert len(diff_set['hard']) > 0

    def test_rapid_sequential_processing(self):
        """測試快速連續處理"""
        processor = AudioProcessor()
        generator = MIDIGenerator()
        engine = DifficultyEngine()

        # 模擬 100 個快速的處理操作
        test_notes = [
            {'midi': 60, 'time': 0, 'duration': 0.5, 'confidence': 0.9},
            {'midi': 62, 'time': 0.5, 'duration': 0.5, 'confidence': 0.85},
        ]

        for _ in range(100):
            midi = generator.create_midi_file(test_notes)
            diff_set = engine.create_difficulty_set(test_notes)

            assert midi is not None
            assert len(diff_set) == 3


class TestDataIntegrity:
    """數據完整性測試"""

    def test_note_sequence_preservation(self):
        """測試音符序列保持完整性"""
        original_notes = [
            {'midi': 60, 'note': 'C4', 'time': 0.0, 'duration': 0.5, 'confidence': 0.95},
            {'midi': 62, 'note': 'D4', 'time': 0.5, 'duration': 0.5, 'confidence': 0.90},
            {'midi': 64, 'note': 'E4', 'time': 1.0, 'duration': 0.5, 'confidence': 0.85},
        ]

        generator = MIDIGenerator()

        # 量化
        quantized = generator.quantize_notes(original_notes)
        assert len(quantized) == len(original_notes)

        # 添加表達力
        expressed = generator.add_expression(quantized)
        assert len(expressed) == len(original_notes)

        # 驗證基本信息保持
        for orig, expr in zip(original_notes, expressed):
            assert expr['midi'] == orig['midi']

    def test_difficulty_distribution(self):
        """測試難度分布正確性"""
        notes = [
            {'midi': 60 + i, 'time': i * 0.2, 'duration': 0.1, 'confidence': 0.9}
            for i in range(50)
        ]

        engine = DifficultyEngine()
        diff_set = engine.create_difficulty_set(notes)

        # 驗證難度關係
        easy_count = len(diff_set['easy'])
        normal_count = len(diff_set['normal'])
        hard_count = len(diff_set['hard'])

        # 一般應該滿足: easy < normal < hard
        assert easy_count <= normal_count
        assert normal_count <= hard_count


class TestOutputFormats:
    """輸出格式測試"""

    def test_midi_file_generation(self, temp_dir=None):
        """測試 MIDI 文件生成"""
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()

        test_notes = [
            {'midi': 60, 'time': 0, 'duration': 0.5, 'confidence': 0.9},
            {'midi': 62, 'time': 0.5, 'duration': 0.5, 'confidence': 0.9},
        ]

        generator = MIDIGenerator()
        output_path = os.path.join(temp_dir, 'output.mid')

        midi = generator.create_midi_file(test_notes, file_path=output_path)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_json_metadata_export(self):
        """測試 JSON 元數據導出"""
        test_notes = [
            {'midi': 60, 'time': 0, 'duration': 0.5, 'confidence': 0.9},
            {'midi': 62, 'time': 0.5, 'duration': 0.5, 'confidence': 0.9},
        ]

        engine = DifficultyEngine()
        generator = MIDIGenerator()

        stats = engine.get_statistics(test_notes)
        playback_info = generator.generate_playback_info(test_notes)

        # 測試可序列化為 JSON
        metadata = {
            'stats': stats,
            'playback_info': playback_info
        }

        json_str = json.dumps(metadata, default=str)
        assert len(json_str) > 0

        loaded = json.loads(json_str)
        assert 'stats' in loaded
        assert 'playback_info' in loaded


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
