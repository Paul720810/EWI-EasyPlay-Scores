"""
EWI EasyPlay - Celery 任務隊列配置
異步處理音訊、MIDI 生成等耗時操作
"""

import logging
from celery import Celery, Task
from celery.result import AsyncResult
import os
from datetime import timedelta
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Celery 應用配置
def create_celery_app(broker_url: Optional[str] = None, result_backend: Optional[str] = None) -> Celery:
    """
    創建 Celery 應用實例

    Args:
        broker_url: 消息代理 URL (預設 Redis)
        result_backend: 結果後端 URL (預設 Redis)

    Returns:
        app: Celery 應用
    """

    broker_url = broker_url or os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = result_backend or os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    app = Celery('ewi_platform')

    # 配置
    app.conf.update(
        broker_url=broker_url,
        result_backend=result_backend,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,

        # 任務配置
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 分鐘硬限制
        task_soft_time_limit=25 * 60,  # 25 分鐘軟限制

        # 重試配置
        task_acks_late=True,
        worker_prefetch_multiplier=1,

        # 定期任務配置
        beat_schedule={
            'cleanup-old-tasks': {
                'task': 'tasks.cleanup_old_tasks',
                'schedule': timedelta(hours=1),
            },
            'health-check': {
                'task': 'tasks.health_check',
                'schedule': timedelta(minutes=5),
            },
        }
    )

    logger.info(f"Celery 應用已創建 (Broker: {broker_url})")
    return app


# 創建應用實例
celery_app = create_celery_app()


# 自定義任務基類
class CallbackTask(Task):
    """支持回調的任務基類"""

    def on_success(self, retval, task_id, args, kwargs):
        """任務成功時的回調"""
        logger.info(f"任務 {task_id} 成功完成")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任務重試時的回調"""
        logger.warning(f"任務 {task_id} 重試 (錯誤: {exc})")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗時的回調"""
        logger.error(f"任務 {task_id} 失敗 (錯誤: {exc})")


# 設置任務基類
celery_app.Task = CallbackTask


# 音訊處理任務
@celery_app.task(bind=True, max_retries=3)
def process_audio_task(self, file_path: str, task_config: Dict = None):
    """
    異步處理音訊文件

    Args:
        file_path: 音訊文件路徑
        task_config: 任務配置

    Returns:
        result: 處理結果
    """
    try:
        from core.audio_processor import AudioProcessor

        config = task_config or {}
        logger.info(f"開始處理音訊: {file_path}")

        # 更新任務狀態
        self.update_state(state='PROCESSING', meta={'status': '加載音訊...'})

        processor = AudioProcessor()
        y, sr = processor.load_audio(file_path)

        # 更新任務狀態
        self.update_state(state='PROCESSING', meta={'status': '提取特徵...'})

        features = processor.extract_features(y, sr)

        # 更新任務狀態
        self.update_state(state='PROCESSING', meta={'status': '檢測節奏...'})

        tempo, beats = processor.get_tempo_and_beats(y, sr)

        result = {
            'file_path': file_path,
            'duration': len(y) / sr,
            'sample_rate': sr,
            'features': {
                'mfcc': features.get('mfcc_mean'),
                'chroma': features.get('chroma_mean'),
                'spectral': features.get('spectral_mean')
            },
            'tempo': float(tempo),
            'beat_frames': int(len(beats)),
            'status': 'completed'
        }

        logger.info(f"音訊處理完成: {file_path}")
        return result

    except Exception as exc:
        logger.error(f"音訊處理失敗: {exc}")

        # 重試
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** retry_count))

        return {'status': 'failed', 'error': str(exc)}


# 音高檢測任務
@celery_app.task(bind=True, max_retries=2)
def detect_pitch_task(self, file_path: str, **kwargs):
    """
    異步檢測音高

    Args:
        file_path: 音訊文件路徑

    Returns:
        result: 音符序列
    """
    try:
        from core.audio_processor import AudioProcessor
        from core.pitch_detector import PitchDetector

        logger.info(f"開始檢測音高: {file_path}")
        self.update_state(state='PROCESSING', meta={'status': '加載音訊...'})

        processor = AudioProcessor()
        y, sr = processor.load_audio(file_path)

        self.update_state(state='PROCESSING', meta={'status': '檢測音高...'})

        detector = PitchDetector(sr=sr)
        notes, f0, confidence = detector.extract_note_sequence(y, sr, min_confidence=0.5)

        stats = detector.get_statistics(notes)

        result = {
            'file_path': file_path,
            'notes': notes,
            'statistics': stats,
            'status': 'completed'
        }

        logger.info(f"音高檢測完成: 找到 {len(notes)} 個音符")
        return result

    except Exception as exc:
        logger.error(f"音高檢測失敗: {exc}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)

        return {'status': 'failed', 'error': str(exc)}


# MIDI 生成任務
@celery_app.task(bind=True)
def generate_midi_task(self, notes: list, output_path: str, **kwargs):
    """
    異步生成 MIDI 文件

    Args:
        notes: 音符列表
        output_path: 輸出文件路徑

    Returns:
        result: MIDI 文件信息
    """
    try:
        from core.midi_generator import MIDIGenerator

        logger.info(f"開始生成 MIDI: {output_path}")
        self.update_state(state='PROCESSING', meta={'status': '量化音符...'})

        generator = MIDIGenerator()

        # 量化音符
        quantized_notes = generator.quantize_notes(notes, quantize_level=16)

        self.update_state(state='PROCESSING', meta={'status': '添加表達力...'})

        # 添加表達力
        expressed_notes = generator.add_expression(quantized_notes, expression_type='dynamics')

        self.update_state(state='PROCESSING', meta={'status': '生成 MIDI 文件...'})

        # 生成 MIDI 文件
        midi = generator.create_midi_file(expressed_notes, file_path=output_path)

        playback_info = generator.generate_playback_info(expressed_notes)

        result = {
            'output_path': output_path,
            'note_count': len(expressed_notes),
            'playback_info': playback_info,
            'status': 'completed'
        }

        logger.info(f"MIDI 生成完成: {output_path}")
        return result

    except Exception as exc:
        logger.error(f"MIDI 生成失敗: {exc}")
        return {'status': 'failed', 'error': str(exc), 'output_path': output_path}


# 難度分級任務
@celery_app.task(bind=True)
def grade_difficulty_task(self, notes: list, **kwargs):
    """
    異步進行難度分級

    Args:
        notes: 原始音符列表

    Returns:
        result: 多難度版本
    """
    try:
        from core.difficulty_engine import DifficultyEngine

        logger.info(f"開始難度分級: {len(notes)} 個音符")
        self.update_state(state='PROCESSING', meta={'status': '分析難度...'})

        engine = DifficultyEngine()

        difficulty_set = engine.create_difficulty_set(notes)
        stats = engine.get_statistics(notes)
        difficulty_score = engine.estimate_difficulty_score(notes)

        result = {
            'easy': difficulty_set['easy'],
            'normal': difficulty_set['normal'],
            'hard': difficulty_set['hard'],
            'statistics': stats,
            'difficulty_score': difficulty_score,
            'status': 'completed'
        }

        logger.info(f"難度分級完成")
        return result

    except Exception as exc:
        logger.error(f"難度分級失敗: {exc}")
        return {'status': 'failed', 'error': str(exc)}


# 完整的處理管道任務
@celery_app.task(bind=True)
def process_music_pipeline(self, file_path: str, output_dir: str = '/tmp', **kwargs):
    """
    完整的音樂處理管道
    音訊 → 音高檢測 → MIDI 生成 → 難度分級

    Args:
        file_path: 音訊文件路徑
        output_dir: 輸出目錄

    Returns:
        result: 最終結果
    """
    try:
        import os
        from pathlib import Path

        logger.info(f"開始完整音樂處理管道: {file_path}")

        # 步驟 1: 處理音訊
        self.update_state(state='PROCESSING', meta={'status': '步驟 1/4: 處理音訊...'})
        audio_result = process_audio_task.apply(args=[file_path]).get(timeout=300)

        # 步驟 2: 檢測音高
        self.update_state(state='PROCESSING', meta={'status': '步驟 2/4: 檢測音高...'})
        pitch_result = detect_pitch_task.apply(args=[file_path]).get(timeout=600)

        notes = pitch_result.get('notes', [])

        # 步驟 3: 難度分級
        self.update_state(state='PROCESSING', meta={'status': '步驟 3/4: 難度分級...'})
        difficulty_result = grade_difficulty_task.apply(args=[notes]).get(timeout=120)

        # 步驟 4: 生成 MIDI
        self.update_state(state='PROCESSING', meta={'status': '步驟 4/4: 生成 MIDI...'})

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        base_name = Path(file_path).stem

        midi_tasks = {}
        for difficulty in ['easy', 'normal', 'hard']:
            diff_notes = difficulty_result.get(difficulty, [])
            output_path = os.path.join(output_dir, f"{base_name}_{difficulty}.mid")

            midi_result = generate_midi_task.apply(
                args=[diff_notes, output_path]
            ).get(timeout=120)

            midi_tasks[difficulty] = midi_result

        final_result = {
            'status': 'completed',
            'audio_info': audio_result,
            'pitch_info': {
                'notes_count': len(notes),
                'statistics': pitch_result.get('statistics')
            },
            'difficulty_info': {
                'score': difficulty_result.get('difficulty_score'),
                'counts': {
                    'easy': len(difficulty_result.get('easy', [])),
                    'normal': len(difficulty_result.get('normal', [])),
                    'hard': len(difficulty_result.get('hard', []))
                }
            },
            'midi_files': midi_tasks,
            'output_directory': output_dir
        }

        logger.info(f"完整音樂處理管道完成")
        return final_result

    except Exception as exc:
        logger.error(f"管道處理失敗: {exc}")
        return {'status': 'failed', 'error': str(exc)}


# 任務監控和管理
class TaskManager:
    """任務管理器"""

    @staticmethod
    def get_task_status(task_id: str) -> Dict:
        """
        獲取任務狀態

        Args:
            task_id: 任務 ID

        Returns:
            status: 任務狀態信息
        """
        result = AsyncResult(task_id, app=celery_app)

        return {
            'task_id': task_id,
            'state': result.state,
            'current': result.info.get('current', 0) if isinstance(result.info, dict) else 0,
            'total': result.info.get('total', 0) if isinstance(result.info, dict) else 0,
            'status': result.info.get('status', '') if isinstance(result.info, dict) else str(result.info),
            'result': result.result if result.successful() else None
        }

    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """
        取消任務

        Args:
            task_id: 任務 ID

        Returns:
            success: 是否成功
        """
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        return True

    @staticmethod
    def get_active_tasks() -> list:
        """
        獲取活躍任務列表

        Returns:
            tasks: 活躍任務列表
        """
        inspect = celery_app.control.inspect()
        return inspect.active()


# 清理任務
@celery_app.task
def cleanup_old_tasks():
    """清理過期的任務結果"""
    logger.info("開始清理過期的任務結果")
    # 實現清理邏輯
    pass


# 健康檢查
@celery_app.task
def health_check():
    """進行健康檢查"""
    logger.info("執行 Celery 健康檢查")
    return {'status': 'healthy', 'timestamp': str(__import__('datetime').datetime.now())}
