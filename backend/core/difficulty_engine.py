"""
EWI EasyPlay - 難度分級引擎
根據原始音符序列生成不同難度的版本
"""

import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from utils.constants import DIFFICULTY_LEVELS, EWI_MIN_NOTE, EWI_MAX_NOTE

logger = logging.getLogger(__name__)


class DifficultyEngine:
    """難度分級引擎"""

    def __init__(self):
        """初始化難度分級引擎"""
        self.difficulty_levels = DIFFICULTY_LEVELS
        logger.info("初始化 DifficultyEngine")

    def grade_notes(
        self,
        notes: List[Dict],
        difficulty: str = 'normal'
    ) -> List[Dict]:
        """
        根據難度分級對音符進行處理

        Args:
            notes: 原始音符列表
            difficulty: 難度級別 ('easy', 'normal', 'hard')

        Returns:
            graded_notes: 分級後的音符列表
        """
        try:
            if difficulty.lower() not in self.difficulty_levels:
                logger.warning(f"未知的難度級別: {difficulty}，使用 'normal'")
                difficulty = 'normal'

            config = self.difficulty_levels[difficulty.lower()]

            logger.info(f"對 {len(notes)} 個音符應用 {difficulty} 難度 (保留 {config['note_reduction']*100:.0f}%)")

            # 應用難度特定的處理
            graded = self._apply_difficulty_filter(notes, config)

            # 應用 EWI 特定的最佳化
            optimized = self._optimize_for_ewi(graded, difficulty)

            logger.info(f"難度分級完成: 從 {len(notes)} 個音符縮減到 {len(optimized)} 個")
            return optimized

        except Exception as e:
            logger.error(f"難度分級失敗: {e}")
            return notes

    def _apply_difficulty_filter(
        self,
        notes: List[Dict],
        config: Dict
    ) -> List[Dict]:
        """
        應用難度特定的過濾

        Args:
            notes: 音符列表
            config: 難度配置

        Returns:
            filtered_notes: 過濾後的音符
        """
        try:
            if not notes:
                return []

            # 計算要保留的音符數量
            retention_ratio = config['note_reduction']
            target_count = max(1, int(len(notes) * retention_ratio))

            # 根據置信度和重要性選擇音符
            scored_notes = []

            for i, note in enumerate(notes):
                # 計算音符的"重要性"分數
                score = 0

                # 1. 置信度分數 (最重要)
                confidence = note.get('confidence', 0.5)
                score += confidence * 100

                # 2. 持續時間分數 (較長的音符更重要)
                duration = note.get('duration', 0.5)
                score += min(duration * 50, 50)

                # 3. 強調首尾音符
                if i == 0 or i == len(notes) - 1:
                    score += 30

                # 4. 避免重複 (同一 MIDI 音符)
                if i > 0 and notes[i-1]['midi'] == note['midi']:
                    score -= 20

                # 5. 音符多樣性 (不同的 MIDI 音符更重要)
                nearby_same = sum(
                    1 for j, n in enumerate(notes)
                    if abs(j - i) <= 3 and n['midi'] == note['midi']
                )
                score -= nearby_same * 10

                scored_notes.append((score, i, note))

            # 按分數排序並選擇前 target_count
            scored_notes.sort(key=lambda x: x[0], reverse=True)
            selected_notes = scored_notes[:target_count]

            # 按原始順序排序
            selected_notes.sort(key=lambda x: x[1])

            return [note for _, _, note in selected_notes]

        except Exception as e:
            logger.error(f"難度過濾失敗: {e}")
            return notes

    def _optimize_for_ewi(
        self,
        notes: List[Dict],
        difficulty: str
    ) -> List[Dict]:
        """
        針對 EWI 樂器進行最佳化

        Args:
            notes: 音符列表
            difficulty: 難度級別

        Returns:
            optimized_notes: 最佳化後的音符
        """
        try:
            optimized = []

            for i, note in enumerate(notes):
                opt_note = note.copy()

                # 1. 限制音符到 EWI 範圍
                midi_note = opt_note.get('midi', 60)

                # 轉換為簡單的音符名稱處理
                midi_note = max(40, min(76, midi_note))  # E2 (40) to E5 (76)
                opt_note['midi'] = midi_note

                # 2. 調整音符持續時間
                if difficulty == 'easy':
                    # 輕鬆難度: 延長音符，使其更容易演奏
                    opt_note['duration'] = opt_note.get('duration', 0.5) * 1.2
                    opt_note['velocity'] = 80

                elif difficulty == 'hard':
                    # 困難難度: 縮短音符，增加挑戰
                    opt_note['duration'] = opt_note.get('duration', 0.5) * 0.8
                    opt_note['velocity'] = 100

                else:
                    # 一般難度: 保持原始
                    opt_note['velocity'] = 90

                # 3. 避免連續的大音程跳躍 (在簡單模式下)
                if difficulty == 'easy' and i > 0:
                    prev_midi = optimized[i-1].get('midi', 60)
                    curr_midi = opt_note.get('midi', 60)

                    interval = abs(curr_midi - prev_midi)
                    if interval > 12:  # 超過一個八度
                        # 嘗試找到更接近的替代音符
                        opt_note['midi'] = prev_midi + np.sign(curr_midi - prev_midi) * 7

                # 4. 添加指法提示
                opt_note['fingering'] = self._suggest_fingering(
                    opt_note.get('midi', 60),
                    i,
                    len(notes)
                )

                optimized.append(opt_note)

            logger.debug(f"為 {len(optimized)} 個音符添加了 EWI 最佳化")
            return optimized

        except Exception as e:
            logger.error(f"EWI 最佳化失敗: {e}")
            return notes

    def _suggest_fingering(
        self,
        midi_note: int,
        position: int,
        total_notes: int
    ) -> Dict:
        """
        建議 EWI 指法

        Args:
            midi_note: MIDI 音符
            position: 音符在序列中的位置
            total_notes: 總音符數

        Returns:
            fingering: 指法提示
        """
        try:
            # EWI 的標準指法 (簡化版本)
            fingering_map = {
                # C3-C4 八度
                36: {'fingering': 'XoXoXoXo', 'hand': 'left'},
                37: {'fingering': 'XoXoXoXo', 'hand': 'left'},
                38: {'fingering': 'XoXoXoXo', 'hand': 'left'},
                # ... 實際上需要完整的對應表
                60: {'fingering': 'C (middle)'},  # C4
                62: {'fingering': 'D'},
                64: {'fingering': 'E'},
                65: {'fingering': 'F'},
                67: {'fingering': 'G'},
                69: {'fingering': 'A'},
                71: {'fingering': 'B'},
                72: {'fingering': 'C (high)'},
            }

            return fingering_map.get(
                midi_note,
                {'fingering': f'MIDI {midi_note}', 'hand': 'both'}
            )

        except Exception as e:
            logger.error(f"指法建議失敗: {e}")
            return {'fingering': 'Unknown', 'hand': 'both'}

    def create_difficulty_set(
        self,
        notes: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        為單一音符序列創建完整的難度集合

        Args:
            notes: 原始音符列表

        Returns:
            difficulty_set: {'easy': [...], 'normal': [...], 'hard': [...]}
        """
        try:
            result = {}

            for difficulty in self.difficulty_levels.keys():
                graded = self.grade_notes(notes, difficulty)
                result[difficulty] = graded

            logger.info(f"創建了難度集合: Easy={len(result['easy'])}, "
                       f"Normal={len(result['normal'])}, Hard={len(result['hard'])} 音符")

            return result

        except Exception as e:
            logger.error(f"難度集合創建失敗: {e}")
            return {
                'easy': [],
                'normal': [],
                'hard': []
            }

    def estimate_difficulty_score(self, notes: List[Dict]) -> float:
        """
        估計音符序列的難度分數

        Args:
            notes: 音符列表

        Returns:
            score: 難度分數 (0-100)
        """
        try:
            if not notes:
                return 0.0

            score = 0.0

            # 1. 音符數量 (越多越難)
            note_count_score = min(len(notes) / 100 * 20, 20)  # Max 20 points
            score += note_count_score

            # 2. 音符速率 (越快越難)
            total_duration = max([n.get('time', 0) + n.get('duration', 0) for n in notes])
            if total_duration > 0:
                note_rate = len(notes) / total_duration
                rate_score = min(note_rate / 5 * 20, 20)  # Max 20 points
                score += rate_score

            # 3. 音程跳躍 (越大越難)
            max_jump = 0
            for i in range(len(notes) - 1):
                jump = abs(notes[i+1].get('midi', 60) - notes[i].get('midi', 60))
                max_jump = max(max_jump, jump)

            jump_score = min(max_jump / 12 * 20, 20)  # Max 20 points
            score += jump_score

            # 4. 動態難度 (多種 MIDI 音符)
            unique_notes = len(set(n.get('midi', 60) for n in notes))
            dynamic_score = min(unique_notes / 12 * 20, 20)  # Max 20 points
            score += dynamic_score

            # 5. 平均置信度 (低置信度意味著更難)
            avg_confidence = np.mean([n.get('confidence', 0.5) for n in notes])
            confidence_score = (1 - avg_confidence) * 20  # Max 20 points
            score += confidence_score

            return float(min(score, 100.0))

        except Exception as e:
            logger.error(f"難度估計失敗: {e}")
            return 50.0

    def get_statistics(self, notes: List[Dict]) -> Dict:
        """
        獲取音符序列的統計信息

        Args:
            notes: 音符列表

        Returns:
            stats: 統計信息
        """
        try:
            if not notes:
                return {
                    'total_notes': 0,
                    'unique_notes': 0,
                    'total_duration': 0,
                    'average_note_duration': 0,
                    'difficulty_score': 0,
                    'midi_range': '0-0',
                    'average_confidence': 0
                }

            midi_values = [n.get('midi', 60) for n in notes]
            durations = [n.get('duration', 0.5) for n in notes]

            return {
                'total_notes': len(notes),
                'unique_notes': len(set(midi_values)),
                'total_duration': float(sum(durations)),
                'average_note_duration': float(np.mean(durations)),
                'difficulty_score': self.estimate_difficulty_score(notes),
                'midi_range': f"{min(midi_values)}-{max(midi_values)}",
                'average_confidence': float(np.mean([n.get('confidence', 0.5) for n in notes]))
            }

        except Exception as e:
            logger.error(f"統計計算失敗: {e}")
            return {
                'total_notes': len(notes),
                'unique_notes': 0,
                'total_duration': 0,
                'average_note_duration': 0,
                'difficulty_score': 0,
                'midi_range': '0-0',
                'average_confidence': 0
            }
