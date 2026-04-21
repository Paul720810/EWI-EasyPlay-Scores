"""
EWI 專案常數定義

定義所有應用程序範圍的常量
"""

# ===== 音訊處理常數 =====
SAMPLE_RATE = 22050  # 采樣率 (Hz)
N_MFCC = 13  # MFCC 係數數量
MAX_AUDIO_DURATION = 300  # 最大音訊時長 (秒) = 5 分鐘
MIN_AUDIO_DURATION = 3  # 最小音訊時長 (秒)

# ===== 音高檢測常數 =====
MIN_FREQUENCY = 40  # 最低檢測頻率 (Hz) - EWI 低音
MAX_FREQUENCY = 1000  # 最高檢測頻率 (Hz) - EWI 高音
PITCH_CONFIDENCE_THRESHOLD = 0.9  # 音高檢測置信度閾值

# ===== 難度設置 =====
DIFFICULTY_LEVELS = {
    'easy': {
        'name': '簡單',
        'description': '初學者級別，大幅簡化音符',
        'note_reduction': 0.4,  # 保留 40% 的原始音符
        'min_duration': 0.5,  # 最短音符時長 (秒)
        'transposition': 0,  # 轉調
    },
    'normal': {
        'name': '普通',
        'description': '中等難度，適度簡化',
        'note_reduction': 0.7,  # 保留 70% 的原始音符
        'min_duration': 0.25,
        'transposition': 0,
    },
    'hard': {
        'name': '困難',
        'description': '高難度，盡量保留原始旋律',
        'note_reduction': 0.95,  # 保留 95% 的原始音符
        'min_duration': 0.125,
        'transposition': 0,
    }
}

# ===== EWI 特定常數 =====
EWI_MIN_NOTE = 'E3'  # EWI 最低音
EWI_MAX_NOTE = 'E7'  # EWI 最高音
EWI_PREFERRED_KEYS = ['C', 'F', 'Bb', 'Eb', 'Ab', 'Db']  # EWI 友善的調性

# ===== 簡譜生成常數 =====
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
TEMPO_RANGE = (60, 180)  # 允許的 BPM 範圍
DEFAULT_TEMPO = 120  # 默認 BPM

# ===== MIDI 相關常數 =====
MIDI_PROGRAM_NUMBER = 24  # 笛子音色 (MIDI 程序號)
MIDI_VELOCITY = 90  # 標準力度
MIDI_VELOCITY_NORMAL = 80  # 正常力度
MIDI_VELOCITY_EMPHASIS = 100  # 強調力度
TICKS_PER_BEAT = 480  # 每拍的 MIDI 時鐘

# ===== 文件存儲常數 =====
MAX_UPLOAD_SIZE = 102400000  # 100 MB
UPLOAD_FOLDER = './uploads'
TEMP_FOLDER = './temp'
CACHE_FOLDER = './cache'

ALLOWED_AUDIO_FORMATS = {
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'flac': 'audio/flac',
    'ogg': 'audio/ogg',
    'm4a': 'audio/mp4',
}

# ===== 任務隊列常數 =====
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_TIMEOUT = 600  # 任務超時 (秒) = 10 分鐘

# ===== API 相關常數 =====
API_VERSION = '1.0.0'
API_TITLE = 'EWI EasyPlay Scores API'
API_DESCRIPTION = 'EWI 智能簡譜生成 API - 將音樂轉換為 EWI 練習譜'

# ===== 日誌常數 =====
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# ===== 資料庫常數 =====
DATABASE_PATH = './data/ewi.db'
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# ===== 用戶進度跟踪常數 =====
MAX_ATTEMPTS_PER_SONG = 100  # 每首歌最多練習次數
PERFECT_SCORE_THRESHOLD = 95  # 完美分數的閾值 (%)

# ===== WebSocket 常數 =====
WEBSOCKET_PING_INTERVAL = 30  # 心跳間隔 (秒)
WEBSOCKET_TIMEOUT = 120  # WebSocket 超時 (秒)

# ===== 緩存常數 =====
CACHE_TTL_SHEET = 86400  # 簡譜快取時長 (秒) = 1 天
CACHE_TTL_MIDI = 604800  # MIDI 快取時長 (秒) = 7 天
CACHE_TTL_FEATURE = 86400  # 特徵快取時長 (秒) = 1 天
