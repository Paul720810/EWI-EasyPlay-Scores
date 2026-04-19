# 🚀 EWI EasyPlay Scores 部署指南

## 🎯 專案概述

**EWI EasyPlay Scores** 是一個專為 EWI 玩家設計的智能多版本互動簡譜神器，支援 YouTube 和 Spotify 音樂自動轉換為三種難度的簡譜。

## 📋 部署前準備

### 1. 必要的 API 金鑰

在開始部署前，你需要申請以下 API 金鑰：

#### Spotify API (必需)
1. 前往 [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. 創建新應用程式
3. 獲取 `Client ID` 和 `Client Secret`
4. 設定重定向 URI: `http://localhost:8000/api/spotify/callback`

#### 可選的 AI API (增強功能)
- **GROQ API**: [https://console.groq.com](https://console.groq.com)
- **NVIDIA API**: [https://build.nvidia.com](https://build.nvidia.com)
- **Google API**: [https://console.cloud.google.com](https://console.cloud.google.com)

### 2. 環境配置

複製環境變數範本：
```bash
cp .env.example .env
```

編輯 `.env` 文件，填入你的實際 API 金鑰：
```bash
# Spotify 設定 (必需)
SPOTIFY_CLIENT_ID=your_actual_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_actual_spotify_client_secret

# 可選的 AI API
GROQ_API_KEY=your_groq_api_key
NVIDIA_API_KEY=your_nvidia_api_key
GOOGLE_API_KEY=your_google_api_key

# 網域設定
DOMAIN_NAME=paul720810.dpdns.org
```

## 🐳 Docker 部署 (推薦)

### 本地開發環境

```bash
# 1. 克隆專案
git clone https://github.com/Paul720810/EWI-EasyPlay-Scores.git
cd EWI-EasyPlay-Scores

# 2. 配置環境變數
cp .env.example .env
# 編輯 .env 文件

# 3. 一鍵啟動
./scripts/deployment/deploy-local.sh

# 4. 訪問服務
# 前端: http://localhost
# 後端: http://localhost:8000
# API 文件: http://localhost:8000/docs
```

### 生產環境部署

```bash
# 1. 確保 Docker 和 Docker Compose 已安裝
docker --version
docker-compose --version

# 2. 設定生產環境變數
cp .env.example .env
# 編輯 .env，設定 DEBUG=False

# 3. 啟動生產服務
docker-compose up -d --build

# 4. 檢查服務狀態
docker-compose ps
docker-compose logs -f
```

## ☁️ 雲端部署

### OCI (Oracle Cloud Infrastructure) 部署

你的 OCI 配置：
- **公用 IP**: 140.245.126.35
- **使用者**: opc
- **SSH 金鑰**: 已配置

```bash
# 1. 連接到 OCI 伺服器
ssh opc@140.245.126.35

# 2. 克隆專案
git clone https://github.com/Paul720810/EWI-EasyPlay-Scores.git
cd EWI-EasyPlay-Scores

# 3. 配置環境變數
cp .env.example .env
# 編輯 .env 文件

# 4. 執行部署腳本
./scripts/deployment/deploy-to-oci.sh
```

### Cloudflare Pages (前端)

1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 前往 Pages 頁面
3. 連接 GitHub 倉庫: `Paul720810/EWI-EasyPlay-Scores`
4. 設定建置配置：
   - **建置命令**: `cd frontend && npm install && npm run build`
   - **建置輸出目錄**: `frontend/dist`
   - **根目錄**: `/`

## 🔧 手動安裝

### 系統需求

- Python 3.9+
- Node.js 18+
- FFmpeg
- Redis (可選)

### 後端設置

```bash
cd backend

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 配置環境變數
cp ../.env.example ../.env
# 編輯 .env 文件

# 啟動服務
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端設置

```bash
cd frontend

# 安裝依賴
npm install

# 開發模式
npm run dev

# 或建置生產版本
npm run build
npm run preview
```

## 🔍 驗證部署

### 健康檢查

```bash
# 檢查後端健康狀態
curl http://localhost:8000/health

# 檢查前端
curl http://localhost

# 檢查 API 文件
open http://localhost:8000/docs
```

### 功能測試

1. **YouTube 轉譜測試**:
   - 訪問前端頁面
   - 貼上 YouTube 連結
   - 點擊「開始轉譜」
   - 等待處理完成

2. **Spotify 功能測試**:
   - 點擊「連接 Spotify」
   - 完成 OAuth 認證
   - 搜尋音樂並錄製

## 🚨 常見問題

### 1. Docker 容器無法啟動

```bash
# 檢查日誌
docker-compose logs backend
docker-compose logs frontend

# 重新建置
docker-compose down
docker-compose up --build -d
```

### 2. Spotify 認證失敗

- 確認 `SPOTIFY_CLIENT_ID` 和 `SPOTIFY_CLIENT_SECRET` 正確
- 檢查重定向 URI 設定
- 確認 Spotify 應用程式狀態為 "Development" 或 "Live"

### 3. YouTube 下載失敗

- 確認網路連線正常
- 檢查 YouTube 連結有效性
- 查看後端日誌了解詳細錯誤

### 4. 記憶體不足

```bash
# 增加 Docker 記憶體限制
# 在 docker-compose.yml 中添加：
services:
  backend:
    mem_limit: 2g
    memswap_limit: 2g
```

## 📊 監控和維護

### 日誌查看

```bash
# Docker 日誌
docker-compose logs -f backend
docker-compose logs -f frontend

# 系統日誌
tail -f backend/logs/app.log
```

### 效能監控

```bash
# 檢查系統資源
docker stats

# 檢查磁碟空間
df -h

# 檢查記憶體使用
free -h
```

### 定期維護

```bash
# 清理 Docker 映像
docker system prune -f

# 清理臨時檔案
rm -rf backend/temp/*
rm -rf backend/output/*

# 更新代碼
git pull origin main
docker-compose up --build -d
```

## 🔐 安全建議

1. **環境變數保護**:
   - 絕不將 `.env` 文件提交到 Git
   - 定期更換 API 金鑰
   - 使用強密碼作為 `SECRET_KEY`

2. **網路安全**:
   - 配置防火牆規則
   - 使用 HTTPS (建議配置 SSL 憑證)
   - 限制 API 訪問頻率

3. **資料保護**:
   - 定期備份資料庫
   - 自動清理臨時檔案
   - 監控磁碟使用量

## 📞 支援和幫助

- **GitHub Issues**: [https://github.com/Paul720810/EWI-EasyPlay-Scores/issues](https://github.com/Paul720810/EWI-EasyPlay-Scores/issues)
- **文件**: [README.md](README.md)
- **Email**: paul720810@gmail.com

## 🎯 下一步

1. **申請 Spotify Developer 帳號**
2. **配置 API 金鑰**
3. **執行本地測試**
4. **部署到生產環境**
5. **設定監控和備份**

---

**祝你部署順利！🎵**