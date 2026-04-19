from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import os
import uuid
import asyncio
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime, timedelta
import structlog

# 導入自定義模組
from audio_processor import AudioProcessor
from midi_generator import MIDIGenerator
from difficulty_engine import DifficultyEngine
from spotify_integration import SpotifyIntegration
from task_manager import TaskManager
from config import Settings

# 配置日誌
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# 載入設定
settings = Settings()

# 創建 FastAPI 應用
app = FastAPI(
    title="EWI EasyPlay Scores API",
    description="智能多版本互動簡譜神器 - 支援 YouTube 和 Spotify",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態檔案服務
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化處理器
audio_processor = AudioProcessor()
midi_generator = MIDIGenerator()
difficulty_engine = DifficultyEngine()
spotify_integration = SpotifyIntegration()
task_manager = TaskManager()

# Pydantic 模型
class ProcessRequest(BaseModel):
    youtube_url: Optional[str] = None
    spotify_track_id: Optional[str] = None
    title: Optional[str] = None
    difficulty_levels: List[str] = Field(default=["easy", "normal", "hard"])
    recording_duration: Optional[int] = Field(default=30, ge=10, le=180)

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    estimated_remaining: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 健康檢查端點
@app.get("/health")
async def health_check():
    """系統健康檢查"""
    try:
        # 檢查各個服務狀態
        services_status = {
            "audio_processor": "healthy",
            "midi_generator": "healthy", 
            "spotify_integration": await spotify_integration.health_check(),
            "task_manager": task_manager.health_check(),
            "disk_space": check_disk_space(),
            "memory_usage": check_memory_usage()
        }
        
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/")
async def root():
    """API 根端點"""
    return {
        "message": "🎵 EWI EasyPlay Scores API",
        "version": "1.0.0",
        "features": [
            "YouTube 音樂轉譜",
            "Spotify 直接錄製",
            "三版本智能分級",
            "EWI 專屬優化",
            "互動練習模式"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "youtube_process": "/api/process",
            "spotify_search": "/api/spotify/search",
            "spotify_record": "/api/spotify/record-and-process"
        }
    }

# YouTube 處理端點
@app.post("/api/process", response_model=TaskResponse)
async def process_youtube_url(
    request: ProcessRequest, 
    background_tasks: BackgroundTasks
):
    """處理 YouTube 連結，生成三版本簡譜"""
    if not request.youtube_url:
        raise HTTPException(status_code=400, detail="需要提供 YouTube 連結")
    
    # 驗證 YouTube URL
    if not is_valid_youtube_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="無效的 YouTube 連結格式")
    
    task_id = str(uuid.uuid4())
    
    # 創建任務
    task_info = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "source": "youtube",
        "url": request.youtube_url,
        "difficulty_levels": request.difficulty_levels,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    task_manager.create_task(task_id, task_info)
    
    # 加入背景處理
    background_tasks.add_task(
        process_youtube_background, 
        task_id, 
        request
    )
    
    logger.info("YouTube processing task created", task_id=task_id, url=request.youtube_url)
    
    return TaskResponse(
        task_id=task_id,
        status="queued",
        message="YouTube 轉譜任務已加入處理佇列",
        estimated_time=180
    )

# Spotify 相關端點
@app.get("/api/spotify/auth")
async def spotify_auth():
    """Spotify OAuth 認證"""
    try:
        auth_url = spotify_integration.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error("Spotify auth failed", error=str(e))
        raise HTTPException(status_code=500, detail="Spotify 認證失敗")

@app.get("/api/spotify/callback")
async def spotify_callback(code: str):
    """Spotify OAuth 回調"""
    try:
        token_info = await spotify_integration.handle_callback(code)
        return {"access_token": token_info["access_token"]}
    except Exception as e:
        logger.error("Spotify callback failed", error=str(e))
        raise HTTPException(status_code=400, detail="Spotify 認證回調失敗")

@app.get("/api/spotify/search")
async def spotify_search(q: str, limit: int = 20):
    """搜尋 Spotify 音樂"""
    if not q.strip():
        raise HTTPException(status_code=400, detail="搜尋關鍵字不能為空")
    
    try:
        results = await spotify_integration.search_tracks(q, limit)
        return results
    except Exception as e:
        logger.error("Spotify search failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Spotify 搜尋失敗: {str(e)}")

@app.post("/api/spotify/record-and-process", response_model=TaskResponse)
async def spotify_record_and_process(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """錄製 Spotify 音樂並處理"""
    if not request.spotify_track_id:
        raise HTTPException(status_code=400, detail="需要提供 Spotify 音軌 ID")
    
    # 驗證錄製時長
    if not (10 <= request.recording_duration <= 180):
        raise HTTPException(
            status_code=400, 
            detail="錄製時長必須在 10-180 秒之間"
        )
    
    task_id = str(uuid.uuid4())
    
    # 創建任務
    task_info = {
        "task_id": task_id,
        "status": "recording",
        "progress": 0,
        "source": "spotify",
        "track_id": request.spotify_track_id,
        "recording_duration": request.recording_duration,
        "difficulty_levels": request.difficulty_levels,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    task_manager.create_task(task_id, task_info)
    
    # 加入背景處理
    background_tasks.add_task(
        process_spotify_background,
        task_id,
        request
    )
    
    logger.info(
        "Spotify recording task created", 
        task_id=task_id, 
        track_id=request.spotify_track_id,
        duration=request.recording_duration
    )
    
    return TaskResponse(
        task_id=task_id,
        status="recording",
        message="Spotify 錄製轉譜任務已開始",
        estimated_time=request.recording_duration + 120
    )

# 任務狀態查詢
@app.get("/api/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查詢任務處理狀態"""
    task_info = task_manager.get_task(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    return TaskStatus(**task_info)

# 檔案下載
@app.get("/api/download/{task_id}/{file_name}")
async def download_file(task_id: str, file_name: str):
    """下載生成的檔案"""
    task_info = task_manager.get_task(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    if task_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="任務尚未完成")
    
    file_path = os.path.join("output", task_id, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="檔案不存在")
    
    return FileResponse(
        file_path,
        filename=file_name,
        media_type='application/octet-stream'
    )

# 統計資訊
@app.get("/api/stats")
async def get_stats():
    """獲取系統統計資訊"""
    try:
        stats = task_manager.get_statistics()
        return {
            "total_processed": stats["total_tasks"],
            "today_processed": stats["today_tasks"],
            "success_rate": stats["success_rate"],
            "average_processing_time": stats["avg_processing_time"],
            "active_tasks": stats["active_tasks"],
            "system_load": {
                "cpu_usage": get_cpu_usage(),
                "memory_usage": check_memory_usage(),
                "disk_usage": check_disk_space()
            }
        }
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail="統計資訊獲取失敗")

# 背景處理函數
async def process_youtube_background(task_id: str, request: ProcessRequest):
    """YouTube 背景處理任務"""
    try:
        logger.info("Starting YouTube processing", task_id=task_id)
        
        # 更新任務狀態
        task_manager.update_task(task_id, {
            "status": "downloading",
            "progress": 10,
            "current_step": "下載音訊"
        })
        
        # 1. 下載和預處理音訊
        audio_info = await audio_processor.download_and_process(request.youtube_url)
        
        task_manager.update_task(task_id, {
            "status": "separating",
            "progress": 30,
            "current_step": "分離人聲",
            "title": audio_info.get("title", "未知歌曲")
        })
        
        # 2. 分離人聲
        vocals_path = await audio_processor.separate_vocals(audio_info["audio_path"])
        
        task_manager.update_task(task_id, {
            "status": "transcribing",
            "progress": 50,
            "current_step": "轉換 MIDI"
        })
        
        # 3. 轉換為 MIDI
        midi_path = await midi_generator.audio_to_midi(vocals_path)
        cleaned_midi = await midi_generator.clean_midi(midi_path)
        
        task_manager.update_task(task_id, {
            "status": "generating_versions",
            "progress": 70,
            "current_step": "生成三版本簡譜"
        })
        
        # 4. 生成三版本
        versions = difficulty_engine.generate_three_versions(cleaned_midi)
        
        task_manager.update_task(task_id, {
            "status": "finalizing",
            "progress": 90,
            "current_step": "完成處理"
        })
        
        # 5. 儲存結果
        output_dir = os.path.join("output", task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        for difficulty, score in versions.items():
            # 儲存 MIDI
            midi_file = os.path.join(output_dir, f"{difficulty}.mid")
            score.write("midi", midi_file)
            
            # 生成簡譜 PDF
            pdf_file = os.path.join(output_dir, f"{difficulty}.pdf")
            # jianpu_converter.convert_to_jianpu(midi_file, pdf_file)
            
            results[difficulty] = {
                "midi": f"/api/download/{task_id}/{difficulty}.mid",
                "pdf": f"/api/download/{task_id}/{difficulty}.pdf"
            }
        
        # 完成任務
        task_manager.update_task(task_id, {
            "status": "completed",
            "progress": 100,
            "current_step": "完成",
            "results": results
        })
        
        logger.info("YouTube processing completed", task_id=task_id)
        
    except Exception as e:
        logger.error("YouTube processing failed", task_id=task_id, error=str(e))
        task_manager.update_task(task_id, {
            "status": "error",
            "error": str(e)
        })

async def process_spotify_background(task_id: str, request: ProcessRequest):
    """Spotify 背景處理任務"""
    try:
        logger.info("Starting Spotify processing", task_id=task_id)
        
        # 更新任務狀態
        task_manager.update_task(task_id, {
            "status": "recording",
            "progress": 10,
            "current_step": "錄製音訊"
        })
        
        # 1. 錄製 Spotify 音軌
        recording_result = await spotify_integration.record_track(
            request.spotify_track_id,
            request.recording_duration
        )
        
        task_manager.update_task(task_id, {
            "status": "processing",
            "progress": 30,
            "current_step": "處理錄製音訊",
            "title": recording_result.get("track_info", {}).get("name", "未知歌曲")
        })
        
        # 2. 後續處理與 YouTube 相同
        vocals_path = await audio_processor.separate_vocals(recording_result["audio_path"])
        
        task_manager.update_task(task_id, {
            "status": "transcribing",
            "progress": 50,
            "current_step": "轉換 MIDI"
        })
        
        midi_path = await midi_generator.audio_to_midi(vocals_path)
        cleaned_midi = await midi_generator.clean_midi(midi_path)
        
        task_manager.update_task(task_id, {
            "status": "generating_versions",
            "progress": 70,
            "current_step": "生成三版本簡譜"
        })
        
        versions = difficulty_engine.generate_three_versions(cleaned_midi)
        
        # 儲存結果
        output_dir = os.path.join("output", task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        for difficulty, score in versions.items():
            midi_file = os.path.join(output_dir, f"{difficulty}.mid")
            score.write("midi", midi_file)
            
            results[difficulty] = {
                "midi": f"/api/download/{task_id}/{difficulty}.mid"
            }
        
        # 完成任務
        task_manager.update_task(task_id, {
            "status": "completed",
            "progress": 100,
            "current_step": "完成",
            "results": results
        })
        
        logger.info("Spotify processing completed", task_id=task_id)
        
    except Exception as e:
        logger.error("Spotify processing failed", task_id=task_id, error=str(e))
        task_manager.update_task(task_id, {
            "status": "error",
            "error": str(e)
        })

# 工具函數
def is_valid_youtube_url(url: str) -> bool:
    """驗證 YouTube URL"""
    import re
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(youtube_regex.match(url))

def check_disk_space() -> str:
    """檢查磁碟空間"""
    import shutil
    total, used, free = shutil.disk_usage("/")
    return f"{(used / total) * 100:.1f}%"

def check_memory_usage() -> str:
    """檢查記憶體使用量"""
    import psutil
    return f"{psutil.virtual_memory().percent:.1f}%"

def get_cpu_usage() -> str:
    """獲取 CPU 使用率"""
    import psutil
    return f"{psutil.cpu_percent(interval=1):.1f}%"

# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時執行"""
    logger.info("EWI EasyPlay Scores API starting up")
    
    # 創建必要目錄
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # 初始化服務
    await spotify_integration.initialize()
    task_manager.initialize()
    
    logger.info("EWI EasyPlay Scores API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時執行"""
    logger.info("EWI EasyPlay Scores API shutting down")
    
    # 清理資源
    await spotify_integration.cleanup()
    task_manager.cleanup()
    
    logger.info("EWI EasyPlay Scores API shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
        access_log=True
    )
