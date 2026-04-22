"""
EWI EasyPlay - FastAPI 主應用
集成所有 API 端點和異步處理
"""

import logging
import time
import asyncio

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from pathlib import Path

# 導入自定義服務
try:
    from services import task_manager, audio_processor
except ImportError:
    # 如果 services.py 不存在，使用內聯模擬
    task_manager = None
    audio_processor = None

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="EWI EasyPlay Scores API",
    description="AI 音樂轉 EWI 運指系統",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建必要目錄
Path("temp").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)

# ==================== 簡易任務管理 ====================
class SimpleTaskManager:
    """簡易任務管理器"""
    def __init__(self):
        self.tasks = {}
        self.task_counter = 0
    
    def create_task(self, task_type, **kwargs):
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "status": "processing",
            "progress": 0,
            "current_step": "初始化中...",
            "error": None,
            "results": None,
            **kwargs
        }
        return task_id
    
    def update_task(self, task_id, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
    
    def get_task(self, task_id):
        return self.tasks.get(task_id)
    
    def complete_task(self, task_id, results):
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "完成",
                "results": results
            })
    
    def fail_task(self, task_id, error):
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "error",
                "error": error,
                "current_step": "錯誤"
            })

# 使用服務或簡易版本
if task_manager is None:
    task_manager = SimpleTaskManager()

# 模擬簡譜數據庫
SAMPLE_SHEETS = {
    "easy": {
        "notes": "1 2 3 | 4 5 6 | 7 1' -",
        "fingering": "拇指 | 拇指+食指 | 拇指+食指+中指",
        "tempo": 80
    },
    "normal": {
        "notes": "1 2 3 4 | 5 6 7 1' | 2' 1' 7 6 | 5 - - -",
        "fingering": "基礎指法 + 連音技巧",
        "tempo": 120
    },
    "hard": {
        "notes": "1 3 5 1' | 6 4 2 7 | 1' 6 4 2 | 1 - - -",
        "fingering": "進階指法 + 跳音 + 裝飾音",
        "tempo": 140
    }
}


@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "EWI EasyPlay Scores API v2.0",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "YouTube 音頻下載",
            "音頻旋律分析",
            "簡譜自動生成",
            "MIDI 轉檔"
        ]
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "ewi-backend",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "2.0.0"
    }

# ==================== 異步轉譜 API ====================

@app.post("/api/process")
async def process_audio(
    request: dict,
    background_tasks: BackgroundTasks
):
    """
    處理音頻 - 異步端點
    返回 task_id，前端輪詢 /api/status/{task_id}
    """
    try:
        youtube_url = request.get("youtube_url")
        difficulty_levels = request.get("difficulty_levels", ["easy", "normal", "hard"])
        title = request.get("title", "轉譜結果")
        
        if not youtube_url:
            raise HTTPException(status_code=400, detail="需要提供 YouTube URL")
        
        # 創建任務
        task_id = task_manager.create_task(
            task_type="youtube",
            youtube_url=youtube_url,
            title=title,
            difficulty_levels=difficulty_levels
        )
        
        logger.info(f"任務已創建: {task_id}")
        
        # 異步處理
        background_tasks.add_task(
            process_youtube_task,
            task_id,
            youtube_url,
            difficulty_levels
        )
        
        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "任務已接受，處理中..."
        }
    
    except Exception as e:
        logger.error(f"任務創建失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """獲取任務狀態"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    return task


# ==================== 異步任務執行 ====================

async def process_youtube_task(
    task_id: str,
    youtube_url: str,
    difficulty_levels: List[str]
):
    """背景任務：處理 YouTube 音樂"""
    try:
        logger.info(f"開始處理任務 {task_id}: {youtube_url}")
        
        # 模擬下載和分析
        task_manager.update_task(
            task_id,
            progress=25,
            current_step="下載音頻中..."
        )
        await asyncio.sleep(2)
        
        task_manager.update_task(
            task_id,
            progress=50,
            current_step="分析音頻中..."
        )
        await asyncio.sleep(2)
        
        # 為每個難度生成簡譜和 MIDI
        results = {}
        
        for idx, difficulty in enumerate(difficulty_levels):
            progress = 60 + (idx * 10)
            task_manager.update_task(
                task_id,
                progress=progress,
                current_step=f"生成 {difficulty} 難度簡譜..."
            )
            
            # 獲取簡譜數據
            sheet_data = SAMPLE_SHEETS.get(difficulty, SAMPLE_SHEETS["normal"])
            
            results[difficulty] = {
                "jianpu": sheet_data,
                "midi": f"/data/sample_{difficulty}.mid"
            }
            
            await asyncio.sleep(1)
        
        # 完成任務
        task_manager.complete_task(task_id, results)
        logger.info(f"任務 {task_id} 完成")
    
    except Exception as e:
        logger.error(f"任務 {task_id} 失敗: {str(e)}")
        task_manager.fail_task(task_id, str(e))


# ==================== Spotify API ====================

@app.get("/api/spotify/search")
async def spotify_search(q: str, limit: int = 10):
    """Spotify 搜尋"""
    try:
        mock_tracks = [
            {
                "id": f"track_{i}",
                "name": f"{q} - 結果 {i}",
                "artists": [{"name": "示例藝人"}],
                "album": {
                    "name": "示例專輯",
                    "images": [{"url": "https://via.placeholder.com/300"}]
                }
            }
            for i in range(min(limit, 5))
        ]
        
        return {"tracks": {"items": mock_tracks}}
    
    except Exception as e:
        logger.error(f"Spotify 搜尋失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/spotify/record-and-process")
async def spotify_record_and_process(
    request: dict,
    background_tasks: BackgroundTasks
):
    """Spotify 錄製並轉譜"""
    try:
        task_id = task_manager.create_task(
            task_type="spotify",
            title=request.get("title", "Spotify 音樂")
        )
        
        background_tasks.add_task(
            process_spotify_task,
            task_id,
            request.get("difficulty_levels", ["easy", "normal", "hard"])
        )
        
        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "Spotify 轉譜任務已接受"
        }
    
    except Exception as e:
        logger.error(f"Spotify 處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_spotify_task(task_id: str, difficulty_levels: List[str]):
    """背景任務：處理 Spotify 音樂"""
    try:
        task_manager.update_task(task_id, progress=20, current_step="錄製中...")
        await asyncio.sleep(3)
        
        results = {}
        for difficulty in difficulty_levels:
            results[difficulty] = {
                "jianpu": SAMPLE_SHEETS.get(difficulty, SAMPLE_SHEETS["normal"]),
                "midi": None
            }
        
        task_manager.complete_task(task_id, results)
    
    except Exception as e:
        logger.error(f"Spotify 任務失敗: {str(e)}")
        task_manager.fail_task(task_id, str(e))


# ==================== 本地音檔上傳 ====================

@app.post("/api/upload-audio")
async def upload_audio(
    audio: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """上傳本地音檔轉譜"""
    try:
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="只支援音頻文件")
        
        task_id = task_manager.create_task(
            task_type="upload",
            filename=audio.filename,
            title=audio.filename
        )
        
        if background_tasks:
            background_tasks.add_task(
                process_upload_task,
                task_id
            )
        
        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "文件已上傳，處理中..."
        }
    
    except Exception as e:
        logger.error(f"上傳失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_upload_task(task_id: str):
    """背景任務：處理上傳的音檔"""
    try:
        task_manager.update_task(task_id, progress=50, current_step="分析中...")
        await asyncio.sleep(2)
        
        results = {}
        for difficulty in ["easy", "normal", "hard"]:
            results[difficulty] = {
                "jianpu": SAMPLE_SHEETS.get(difficulty),
                "midi": None
            }
        
        task_manager.complete_task(task_id, results)
    
    except Exception as e:
        logger.error(f"上傳文件任務失敗: {str(e)}")
        task_manager.fail_task(task_id, str(e))




# ==================== 工具 API ====================

@app.get("/api/difficulties")
async def get_difficulties():
    """獲取可用的難度等級"""
    return {
        "difficulties": [
            {
                "id": "easy",
                "name": "簡單",
                "description": "基礎音符，慢節拍，適合初學者",
                "tempo_range": "60-90 BPM",
                "features": ["基礎指法", "簡單節奏", "常用音階"]
            },
            {
                "id": "normal",
                "name": "普通",
                "description": "標準難度，適合有基礎的演奏者",
                "tempo_range": "90-130 BPM",
                "features": ["標準指法", "連音技巧", "節奏變化"]
            },
            {
                "id": "hard",
                "name": "困難",
                "description": "進階技巧，快節拍，適合熟練演奏者",
                "tempo_range": "130+ BPM",
                "features": ["進階指法", "跳音技巧", "裝飾音", "複雜節奏"]
            }
        ]
    }


@app.get("/api/stats")
async def get_stats():
    """獲取使用統計"""
    return {
        "total_tasks": len(task_manager.tasks),
        "completed_tasks": len([t for t in task_manager.tasks.values() if t["status"] == "completed"]),
        "active_tasks": len([t for t in task_manager.tasks.values() if t["status"] == "processing"]),
        "supported_formats": ["MP3", "WAV", "M4A", "FLAC"],
        "difficulty_levels": ["easy", "normal", "hard"],
        "features": {
            "youtube_download": True,
            "audio_analysis": False,
            "jianpu_generation": True,
            "midi_generation": False,
            "spotify_integration": False,
            "ewi_fingering": False
        }
    }


@app.get("/api/sample-sheet/{difficulty}")
async def get_sample_sheet(difficulty: str):
    """獲取示例簡譜"""
    if difficulty not in SAMPLE_SHEETS:
        raise HTTPException(status_code=404, detail="難度等級不存在")

    sheet_data = SAMPLE_SHEETS[difficulty]
    return {
        "difficulty": difficulty,
        "sheet_music": {
            "title": f"示例簡譜 ({difficulty})",
            "notes": sheet_data["notes"],
            "fingering": sheet_data["fingering"],
            "tempo": sheet_data["tempo"],
            "key": "C",
            "difficulty": difficulty
        }
    }


# ==================== 靜態文件 ====================

if Path("../frontend/dist").exists():
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

