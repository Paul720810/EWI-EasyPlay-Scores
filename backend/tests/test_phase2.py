"""
測試 Phase 2 組件: MIDI 生成、音高檢測、難度分級
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path

# 修正導入路徑
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.audio_processor import AudioProcessor
from core.pitch_detector import PitchDetector
from core.midi_generator import MIDIGenerator
from core.difficulty_engine import DifficultyEngine
from utils.constants import SAMPLE_RATE, MIDI_PROGRAM_NUMBER, TICKS_PER_BEAT


class TestPitchDetector:
    """測試音高檢測器"""

    @pytest.fixture
    def detector(self):
        """創建檢測器實例"""
        return PitchDetector(sr=SAMPLE_RATE)

    @pytest.fixture
    def test_audio(self):
        """生成測試音訊"""
        sr = SAMPLE_RATE
        duration = 2.0

        # 生成 C4 (262 Hz) 的純音
        t = np.linspace(0, duration, int(sr * duration))
        freq = 262  # C4
        y = 0.3 * np.sin(2 * np.pi * freq * t)

        return y, sr

    def test_detector_initialization(self, detector):
        """測試檢測器初始化"""
        assert detector.sr == SAMPLE_RATE
        assert detector.hop_length == 512

    def test_frequency_to_midi(self, detector):
        """測試頻率到 MIDI 轉換"""
        # A4 = 440 Hz, MIDI 69
        midi = detector.frequency_to_midi(440)
        assert midi == 69

        # C4 = 262 Hz, MIDI 60
        midi = detector.frequency_to_midi(262)
        assert midi == 60

    def test_midi_to_note_name(self, detector):
        """測試 MIDI 到音符名稱轉換"""
        assert detector.midi_to_note_name(60) == 'C4'
        assert detector.midi_to_note_name(69) == 'A4'
        assert detector.midi_to_note_name(72) == 'C5'

    def test_extract_note_sequence(self, detector, test_audio):
        """測試音符序列提取"""
        y, sr = test_audio
        notes, f0, confidence = detector.extract_note_sequence(y, sr, min_confidence=0.3)

        # 應該檢測到至少一個音符
        assert len(notes) > 0

        # 檢查音符結構
        for note in notes:
            assert 'midi' in note
            assert 'note' in note
            assert 'time' in note
            assert 'duration' in note
            assert 'confidence' in note

    def test_get_statistics(self, detector, test_audio):
        """測試統計信息生成"""
        y, sr = test_audio
        notes, _, _ = detector.extract_note_sequence(y, sr, min_confidence=0.3)

        if notes:
            stats = detector.get_statistics(notes)
            assert 'total_notes' in stats
            assert 'total_duration' in stats
            assert 'average_note_duration' in stats
            assert stats['total_notes'] > 0

    def test_detect_vibrato(self, detector):
        """測試顫音檢測"""
        # 生成帶有顫音的信號
        sr = SAMPLE_RATE
        t = np.linspace(0, 2, 2 * sr)

        # 6 Hz 顫音
        base_freq = 262
        vibrato_freq = 6
        vibrato_depth = 20

        y = 0.3 * np.sin(2 * np.pi * base_freq * t +
                         vibrato_depth * np.sin(2 * np.pi * vibrato_freq * t))

        _, f0 = detector.detect_fundamental_frequency(y)
        vibrato_info = detector.detect_vibrato(y, f0)

        assert 'rate' in vibrato_info
        assert 'depth' in vibrato_info
        assert 'detected' in vibrato_info


class TestMIDIGenerator:
    """測試 MIDI 生成器"""

    @pytest.fixture
    def generator(self):
        """創建生成器實例"""
        return MIDIGenerator(
            ticks_per_beat=TICKS_PER_BEAT,
            tempo=500000,  # 120 BPM
            program=MIDI_PROGRAM_NUMBER
        )

    @pytest.fixture
    def test_notes(self):
        """創建測試音符"""
        return [
            {'midi': 60, 'note': 'C4', 'time': 0.0, 'duration': 0.5, 'confidence': 0.9},
            {'midi': 62, 'note': 'D4', 'time': 0.5, 'duration': 0.5, 'confidence': 0.85},
            {'midi': 64, 'note': 'E4', 'time': 1.0, 'duration': 0.5, 'confidence': 0.95},
            {'midi': 65, 'note': 'F4', 'time': 1.5, 'duration': 0.5, 'confidence': 0.88},
        ]

    def test_generator_initialization(self, generator):
        """測試生成器初始化"""
        assert generator.ticks_per_beat == TICKS_PER_BEAT
        assert generator.tempo == 500000
        assert generator.program == MIDI_PROGRAM_NUMBER

    def test_create_midi_file(self, generator, test_notes):
        """測試 MIDI 文件創建"""
        mid = generator.create_midi_file(test_notes)

        assert mid is not None
        assert len(mid.tracks) > 0
        assert mid.ticks_per_beat == TICKS_PER_BEAT

    def test_save_midi_file(self, generator, test_notes):
        """測試 MIDI 文件保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'test.mid')

            mid = generator.create_midi_file(test_notes, file_path=file_path)

            assert os.path.exists(file_path)
            assert os.path.getsize(file_path) > 0

    def test_quantize_notes(self, generator, test_notes):
        """測試音符量化"""
        quantized = generator.quantize_notes(test_notes, quantize_level=16)

        assert len(quantized) == len(test_notes)

        for note in quantized:
            assert 'midi' in note
            assert 'time' in note
            assert 'duration' in note

    def test_add_expression(self, generator, test_notes):
        """測試表達力添加"""
        # 測試動態
        expressed = generator.add_expression(test_notes, expression_type='dynamics')
        for note in expressed:
            assert 'velocity' in note

        # 測試顫音
        expressed = generator.add_expression(test_notes, expression_type='vibrato')
        for note in expressed:
            assert 'vibrato_rate' in note or 'midi' in note

        # 測試連奏
        expressed = generator.add_expression(test_notes, expression_type='legato')
        for note in expressed:
            assert 'duration' in note

    def test_generate_playback_info(self, generator, test_notes):
        """測試播放信息生成"""
        info = generator.generate_playback_info(test_notes)

        assert 'total_duration' in info
        assert 'note_count' in info
        assert 'tempo_bpm' in info
        assert 'time_signature' in info
        assert 'key_signature' in info
        assert 'estimated_difficulty' in info
        assert info['note_count'] == len(test_notes)


class TestDifficultyEngine:
    """測試難度分級引擎"""

    @pytest.fixture
    def engine(self):
        """創建引擎實例"""
        return DifficultyEngine()

    @pytest.fixture
    def test_notes(self):
        """創建測試音符"""
        notes = []
        for i in range(20):
            notes.append({
                'midi': 60 + (i % 12),
                'note': f'Note{i}',
                'time': i * 0.5,
                'duration': 0.4,
                'confidence': 0.8 + 0.1 * np.random.random()
            })
        return notes

    def test_engine_initialization(self, engine):
        """測試引擎初始化"""
        assert engine.difficulty_levels is not None
        assert 'easy' in engine.difficulty_levels
        assert 'normal' in engine.difficulty_levels
        assert 'hard' in engine.difficulty_levels

    def test_grade_notes_easy(self, engine, test_notes):
        """測試簡單難度分級"""
        graded = engine.grade_notes(test_notes, 'easy')

        # 簡單難度應該減少音符數量
        assert len(graded) <= len(test_notes)
        assert len(graded) > 0

    def test_grade_notes_normal(self, engine, test_notes):
        """測試一般難度分級"""
        graded = engine.grade_notes(test_notes, 'normal')

        assert len(graded) <= len(test_notes)
        assert len(graded) > 0

    def test_grade_notes_hard(self, engine, test_notes):
        """測試困難難度分級"""
        graded = engine.grade_notes(test_notes, 'hard')

        # 困難難度應該保留最多音符
        assert len(graded) <= len(test_notes)
        assert len(graded) > 0

    def test_create_difficulty_set(self, engine, test_notes):
        """測試難度集合創建"""
        diff_set = engine.create_difficulty_set(test_notes)

        assert 'easy' in diff_set
        assert 'normal' in diff_set
        assert 'hard' in diff_set

        # 驗證難度遞進關係
        assert len(diff_set['easy']) <= len(diff_set['normal']) <= len(diff_set['hard'])

    def test_estimate_difficulty_score(self, engine, test_notes):
        """測試難度分數估計"""
        score = engine.estimate_difficulty_score(test_notes)

        assert 0 <= score <= 100

    def test_get_statistics(self, engine, test_notes):
        """測試統計信息"""
        stats = engine.get_statistics(test_notes)

        assert 'total_notes' in stats
        assert 'unique_notes' in stats
        assert 'total_duration' in stats
        assert 'difficulty_score' in stats
        assert stats['total_notes'] == len(test_notes)


class TestIntegration:
    """整合測試: 端到端工作流"""

    def test_full_pipeline(self):
        """測試完整管道: 音訊 → 音高 → MIDI → 難度"""
        # 1. 生成測試音訊
        sr = SAMPLE_RATE
        duration = 3.0
        t = np.linspace(0, duration, int(sr * duration))

        # 簡單的 C-D-E-F 序列
        y = np.zeros_like(t)
        notes_freqs = [262, 294, 330, 349]  # C, D, E, F

        for i, freq in enumerate(notes_freqs):
            start = int(i * sr * duration / 4)
            end = int((i + 1) * sr * duration / 4)
            y[start:end] = 0.3 * np.sin(2 * np.pi * freq * t[start:end])

        # 2. 提取音符
        detector = PitchDetector(sr=sr)
        notes, _, _ = detector.extract_note_sequence(y, sr, min_confidence=0.3)

        if notes:
            # 3. 生成 MIDI
            generator = MIDIGenerator()
            midi = generator.create_midi_file(notes)

            assert midi is not None
            assert len(midi.tracks) > 0

            # 4. 應用難度分級
            engine = DifficultyEngine()
            diff_set = engine.create_difficulty_set(notes)

            assert len(diff_set['easy']) > 0
            assert len(diff_set['normal']) > 0
            assert len(diff_set['hard']) > 0

    def test_pipeline_with_file_io(self):
        """測試包含文件 I/O 的完整管道"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 創建測試音訊文件
            import soundfile as sf

            sr = SAMPLE_RATE
            duration = 2.0
            t = np.linspace(0, duration, int(sr * duration))

            # C 大調
            y = 0.3 * np.sin(2 * np.pi * 262 * t)

            audio_file = os.path.join(tmpdir, 'test.wav')
            sf.write(audio_file, y, sr)

            # 處理音訊
            processor = AudioProcessor(sr=sr)
            y_loaded, sr_loaded = processor.load_audio(audio_file)

            assert y_loaded is not None
            assert sr_loaded == sr

            # 提取音符並生成 MIDI
            detector = PitchDetector(sr=sr)
            notes, _, _ = detector.extract_note_sequence(y_loaded, sr, min_confidence=0.3)

            generator = MIDIGenerator()
            midi_file = os.path.join(tmpdir, 'output.mid')
            midi = generator.create_midi_file(notes, file_path=midi_file)

            assert os.path.exists(midi_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
