"""
EWI EasyPlay - MIDI 生成引擎
根據音符序列生成標準 MIDI 文件
"""

import logging
from typing import List, Dict, Optional, Tuple
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
import numpy as np
from utils.constants import MIDI_PROGRAM_NUMBER, TICKS_PER_BEAT, MIDI_VELOCITY

logger = logging.getLogger(__name__)


class MIDIGenerator:
    """MIDI 文件生成引擎"""

    def __init__(
        self,
        ticks_per_beat: int = TICKS_PER_BEAT,
        tempo: int = 500000,  # 微秒/拍 (120 BPM)
        channel: int = 0,
        program: int = MIDI_PROGRAM_NUMBER
    ):
        """
        初始化 MIDI 生成器

        Args:
            ticks_per_beat: 每拍的 tick 數
            tempo: 速度 (微秒/拍)
            channel: MIDI 通道 (0-15)
            program: MIDI 程序號 (樂器)
        """
        self.ticks_per_beat = ticks_per_beat
        self.tempo = tempo
        self.channel = channel
        self.program = program

        logger.info(f"初始化 MIDI 生成器 (tempo={self.tempo}, program={program})")

    def create_midi_file(
        self,
        notes: List[Dict],
        tempo_bpm: Optional[int] = None,
        file_path: Optional[str] = None
    ) -> MidiFile:
        """
        從音符序列創建 MIDI 文件

        Args:
            notes: 音符列表 [{'midi': int, 'time': float, 'duration': float, ...}, ...]
            tempo_bpm: 速度 (BPM)，如果為 None 則使用預設值
            file_path: 保存文件路徑，如果提供則保存文件

        Returns:
            midi_file: MidiFile 對象
        """
        try:
            if not notes:
                logger.warning("音符列表為空，返回空 MIDI 文件")
                return self._create_empty_midi()

            # 創建 MIDI 文件
            mid = MidiFile()
            mid.ticks_per_beat = self.ticks_per_beat

            # 創建音軌
            track = MidiTrack()
            mid.tracks.append(track)

            # 設置速度
            if tempo_bpm:
                tempo_us = int(60_000_000 / tempo_bpm)  # 轉換 BPM 到微秒
            else:
                tempo_us = self.tempo

            track.append(MetaMessage('set_tempo', tempo=tempo_us))
            track.append(Message('program_change', program=self.program, channel=self.channel))

            # 排序音符 (按時間)
            sorted_notes = sorted(notes, key=lambda x: x.get('time', 0))

            # 轉換時間為 MIDI tick
            current_time = 0

            for note in sorted_notes:
                midi_note = note['midi']
                note_duration = note.get('duration', 0.5)  # 預設 0.5 秒

                # 轉換時間為 tick
                note_start_time = note.get('time', 0)
                note_start_tick = self._time_to_tick(note_start_time)

                # 計算 delta time
                delta_time = note_start_tick - current_time

                # Note On
                track.append(Message(
                    'note_on',
                    note=midi_note,
                    velocity=MIDI_VELOCITY,
                    time=delta_time,
                    channel=self.channel
                ))

                # Note Off
                note_duration_tick = self._time_to_tick(note_duration)
                track.append(Message(
                    'note_off',
                    note=midi_note,
                    velocity=0,
                    time=note_duration_tick,
                    channel=self.channel
                ))

                current_time = note_start_tick + note_duration_tick

            # 保存文件 (如果提供路徑)
            if file_path:
                mid.save(file_path)
                logger.info(f"MIDI 文件已保存: {file_path}")

            logger.info(f"創建了包含 {len(notes)} 個音符的 MIDI 文件")
            return mid

        except Exception as e:
            logger.error(f"MIDI 文件創建失敗: {e}")
            return self._create_empty_midi()

    def _time_to_tick(self, time_seconds: float) -> int:
        """
        將秒轉換為 MIDI tick

        Args:
            time_seconds: 時間 (秒)

        Returns:
            ticks: MIDI tick 數
        """
        # 假設 tempo 為 120 BPM (500000 微秒/拍 = 0.5 秒/拍)
        beats = time_seconds / (self.tempo / 60_000_000)
        ticks = int(beats * self.ticks_per_beat)
        return max(0, ticks)

    def _create_empty_midi(self) -> MidiFile:
        """創建空 MIDI 文件"""
        mid = MidiFile()
        mid.ticks_per_beat = self.ticks_per_beat
        track = MidiTrack()
        mid.tracks.append(track)
        track.append(MetaMessage('set_tempo', tempo=self.tempo))
        return mid

    def quantize_notes(
        self,
        notes: List[Dict],
        quantize_level: int = 16
    ) -> List[Dict]:
        """
        量化音符到固定網格

        Args:
            notes: 音符列表
            quantize_level: 量化級別 (4, 8, 16, 32)

        Returns:
            quantized_notes: 量化後的音符
        """
        try:
            quantized = []
            min_tick = (self.ticks_per_beat * 4) // quantize_level  # 最小 tick

            for note in notes:
                q_note = note.copy()

                # 量化時間
                time_tick = self._time_to_tick(note.get('time', 0))
                quantized_tick = round(time_tick / min_tick) * min_tick
                q_note['time'] = quantized_tick / (self.ticks_per_beat / 0.25)

                # 量化持續時間
                duration_tick = self._time_to_tick(note.get('duration', 0.5))
                quantized_duration = round(duration_tick / min_tick) * min_tick
                q_note['duration'] = quantized_duration / (self.ticks_per_beat / 0.25)

                quantized.append(q_note)

            logger.info(f"量化了 {len(quantized)} 個音符")
            return quantized

        except Exception as e:
            logger.error(f"音符量化失敗: {e}")
            return notes

    def add_expression(
        self,
        notes: List[Dict],
        expression_type: str = 'dynamics'
    ) -> List[Dict]:
        """
        為音符添加表達力 (動態、顫音等)

        Args:
            notes: 音符列表
            expression_type: 表達類型 ('dynamics', 'vibrato', 'legato')

        Returns:
            notes_with_expression: 添加表達的音符
        """
        try:
            expressed_notes = []

            for i, note in enumerate(notes):
                expr_note = note.copy()

                if expression_type == 'dynamics':
                    # 根據音符序列中的位置動態調整速度
                    position_ratio = i / max(1, len(notes) - 1)
                    velocity = int(64 + 30 * np.sin(position_ratio * np.pi))
                    expr_note['velocity'] = max(1, min(127, velocity))

                elif expression_type == 'vibrato':
                    # 添加顫音標記
                    expr_note['vibrato_rate'] = 6.0  # Hz
                    expr_note['vibrato_depth'] = 50  # cents

                elif expression_type == 'legato':
                    # 延長音符使其連貫
                    if i < len(notes) - 1:
                        next_note_time = notes[i + 1].get('time', 0)
                        expr_note['duration'] = max(
                            expr_note.get('duration', 0),
                            (next_note_time - expr_note.get('time', 0)) * 0.9
                        )

                expressed_notes.append(expr_note)

            logger.info(f"為 {len(expressed_notes)} 個音符添加了 {expression_type} 表達")
            return expressed_notes

        except Exception as e:
            logger.error(f"添加表達失敗: {e}")
            return notes

    def generate_playback_info(self, notes: List[Dict]) -> Dict:
        """
        生成播放信息

        Args:
            notes: 音符列表

        Returns:
            playback_info: 播放信息
        """
        try:
            if not notes:
                return {
                    'total_duration': 0,
                    'note_count': 0,
                    'tempo_bpm': 0,
                    'time_signature': '4/4',
                    'key_signature': 'C',
                    'estimated_difficulty': 'Unknown'
                }

            # 計算總時長
            total_time = max([n.get('time', 0) + n.get('duration', 0) for n in notes])

            # 轉換 tempo
            tempo_bpm = int(60_000_000 / self.tempo)

            # 估計難度 (基於音符數量和速率)
            note_count = len(notes)
            avg_duration = np.mean([n.get('duration', 0.5) for n in notes])
            note_rate = note_count / max(0.1, total_time)  # notes per second

            if note_rate < 2:
                difficulty = 'Easy'
            elif note_rate < 5:
                difficulty = 'Normal'
            else:
                difficulty = 'Hard'

            return {
                'total_duration': float(total_time),
                'note_count': note_count,
                'tempo_bpm': tempo_bpm,
                'time_signature': '4/4',
                'key_signature': 'C',
                'estimated_difficulty': difficulty,
                'note_rate': float(note_rate),
                'average_note_duration': float(avg_duration)
            }

        except Exception as e:
            logger.error(f"生成播放信息失敗: {e}")
            return {
                'total_duration': 0,
                'note_count': len(notes),
                'tempo_bpm': 120,
                'time_signature': '4/4',
                'key_signature': 'C',
                'estimated_difficulty': 'Unknown'
            }
