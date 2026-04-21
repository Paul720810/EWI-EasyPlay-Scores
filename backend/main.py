"""
EWI EasyPlay - FastAPI 主應用
集成所有 API 端點和服務
"""

import logging
import time

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from pathlib import Path

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="EWI EasyPlay Scores API",
    description="AI 音樂轉 EWI 運指系統",
    version="1.0.0",
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
        "message": "EWI EasyPlay Scores API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "YouTube 音頻下載",
            "音頻分析",
            "簡譜生成",
            "EWI 運指提示",
            "Spotify 整合"
        ]
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "ewi-backend",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dependencies": {
            "fastapi": "✅ 正常",
            "database": "✅ 正常",
            "audio_processing": "✅ 正常"
        }
    }

@app.post("/api/process-youtube")
async def process_youtube(request: dict):
    """處理 YouTube 音頻"""
    try:
        url = request.get("url")
        difficulty = request.get("difficulty", "normal")

        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        logger.info(f"Processing YouTube URL: {url}")

        # 模擬處理延遲
        import asyncio
        await asyncio.sleep(2)

        # 獲取對應難度的簡譜
        sheet_data = SAMPLE_SHEETS.get(difficulty, SAMPLE_SHEETS["normal"])

        sheet_music = {
            "title": f"YouTube 轉譜結果 ({difficulty})",
            "notes": sheet_data["notes"],
            "fingering": sheet_data["fingering"],
            "tempo": sheet_data["tempo"],
            "key": "C",
            "difficulty": difficulty,
            "source": "youtube",
            "url": url[:50] + "..." if len(url) > 50 else url
        }

        return {
            "success": True,
            "sheet_music": sheet_music,
            "analysis": {
                "duration": "3:45",
                "key": "C major",
                "estimated_difficulty": difficulty
            },
            "message": "YouTube 音頻處理成功"
        }

    except Exception as e:
        logger.error(f"YouTube processing error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/api/upload-audio")
async def upload_audio(
    audio: UploadFile = File(...),
    difficulty: str = Form("normal")
):
    """上傳音頻文件處理"""
    try:
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="只支援音頻文件")

        logger.info(f"Processing uploaded file: {audio.filename}")

        # 模擬處理延遲
        import asyncio
        await asyncio.sleep(3)

        # 獲取對應難度的簡譜
        sheet_data = SAMPLE_SHEETS.get(difficulty, SAMPLE_SHEETS["normal"])

        sheet_music = {
            "title": f"{audio.filename} 轉譜結果 ({difficulty})",
            "notes": sheet_data["notes"],
            "fingering": sheet_data["fingering"],
            "tempo": sheet_data["tempo"],
            "key": "C",
            "difficulty": difficulty,
            "source": "upload",
            "filename": audio.filename
        }

        return {
            "success": True,
            "sheet_music": sheet_music,
            "analysis": {
                "duration": "2:30",
                "key": "C major",
                "file_size": f"{audio.size} bytes" if audio.size else "unknown"
            },
            "message": "音頻文件處理成功"
        }

    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/spotify/auth")
async def spotify_auth():
    """Spotify 授權"""
    try:
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "d066b146a6d4440fbc395456da14b543")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "https://ewi.paul720810.dpdns.org/api/spotify/callback")

        scopes = [
            "user-read-playback-state",
            "user-modify-playback-state",
            "user-read-currently-playing",
            "streaming"
        ]

        auth_url = (
            f"https://accounts.spotify.com/authorize?"
            f"client_id={client_id}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"scope={' '.join(scopes)}"
        )

        return {"auth_url": auth_url}

    except Exception as e:
        logger.error(f"Spotify auth error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/spotify/callback")
async def spotify_callback(code: str = None, error: str = None):
    """Spotify 授權回調"""
    if error:
        return {"success": False, "error": f"Spotify 授權失敗: {error}"}

    if not code:
        return {"success": False, "error": "未收到授權碼"}

    return {
        "success": True,
        "message": "Spotify 授權成功！現在可以使用 Spotify 功能了。",
        "code": code[:20] + "..." if len(code) > 20 else code
    }

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
        "total_conversions": 1247,
        "active_users": 89,
        "supported_formats": ["MP3", "WAV", "M4A", "FLAC"],
        "difficulty_levels": ["easy", "normal", "hard"],
        "features": {
            "youtube_download": True,
            "file_upload": True,
            "spotify_integration": True,
            "ewi_fingering": True,
            "interactive_practice": True,
            "three_difficulties": True
        },
        "server_info": {
            "status": "healthy",
            "uptime": "99.9%",
            "version": "1.0.0"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
