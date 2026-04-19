from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API 設定
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # 安全設定
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://paul720810.dpdns.org"]
    
    # 檔案路徑
    TEMP_DIR: str = "./temp"
    OUTPUT_DIR: str = "./output"
    STATIC_DIR: str = "./static"
    
    # YouTube 設定
    YOUTUBE_DL_FORMAT: str = "bestaudio/best"
    
    # Spotify 設定
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/api/spotify/callback"
    
    # 處理設定
    MAX_AUDIO_LENGTH: int = 600  # 10 分鐘
    DEMUCS_MODEL: str = "htdemucs"
    BASIC_PITCH_ONSET_THRESHOLD: float = 0.5
    BASIC_PITCH_FRAME_THRESHOLD: float = 0.3
    
    # 錄製設定
    MAX_RECORDING_DURATION: int = 180  # 3 分鐘
    AUTO_DELETE_HOURS: int = 24
    DAILY_RECORDING_LIMIT: int = 10
    
    # 檔案大小限制
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Redis 設定 (用於任務佇列)
    REDIS_URL: str = "redis://localhost:6379"
    
    # 資料庫設定
    DATABASE_URL: str = "sqlite:///./ewi_scores.db"
    
    # 監控設定
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # 日誌設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # 外部 API (從環境變數讀取)
    GROQ_API_KEY: str = ""
    NVIDIA_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 全域設定實例
settings = Settings()
