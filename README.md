# 🎵 EWI EasyPlay Scores

> 智能多版本互動簡譜神器 - 專為 EWI 玩家設計的開源練習工具

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## ✨ 特色功能

- 🎯 **雙平台支援**：YouTube 連結轉譜 + Spotify 直接錄製
- 🎼 **智能三版本分級**：Easy / Normal / Hard 自動適配 EWI 特性
- 🎵 **互動練習模式**：MIDI 播放 + 游標同步 + 歌詞高亮
- 🎹 **EWI 專屬優化**：運指提示 + 換氣記號 + 調性友善化
- 📚 **每日更新歌庫**：公有領域經典歌曲自動入庫
- 🔓 **完全開源**：MIT 授權，可商用、可修改、可自架
- 🚀 **雲端部署**：OCI + Cloudflare + Kaggle GPU 免費架構

## 🌐 線上體驗

**正式網站**: [https://paul720810.dpdns.org](https://paul720810.dpdns.org)

**API 文件**: [https://paul720810.dpdns.org/docs](https://paul720810.dpdns.org/docs)

## 🚀 快速開始

### 方法一：Docker 一鍵部署 (推薦)

```bash
# 克隆專案
git clone https://github.com/Paul720810/EWI-EasyPlay-Scores.git
cd EWI-EasyPlay-Scores

# 一鍵啟動
./scripts/deployment/deploy-local.sh

# 訪問服務
# 前端: http://localhost
# 後端: http://localhost:8000
# API 文件: http://localhost:8000/docs
```

### 方法二：手動安裝

#### 環境需求
- Python 3.9+
- Node.js 18+
- FFmpeg
- Redis (可選，用於任務佇列)

#### 後端設置
```bash
cd backend

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 配置環境變數
cp .env.example .env
# 編輯 .env 文件，填入必要配置

# 啟動服務
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端設置
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

## 📖 使用說明

### YouTube 模式
1. 貼上 YouTube 音樂連結
2. 點擊「開始轉譜」
3. 等待處理完成（約 2-5 分鐘）
4. 選擇難度版本開始練習

### Spotify 模式
1. 點擊「連接 Spotify」並授權
2. 搜尋想要的音樂
3. 選擇錄製時長（10-180 秒）
4. 點擊「錄製並轉譜」
5. 系統自動錄製並轉換為簡譜

### 練習功能
- **播放控制**：播放/暫停/停止
- **速度調整**：0.5x - 1.5x 可調
- **運指提示**：即時顯示 EWI 指法
- **進度跟蹤**：游標同步顯示當前位置
- **檔案下載**：MIDI、PDF、PNG 格式

## 🛠️ 技術架構

### 後端技術棧
- **FastAPI** - 現代 Python Web 框架
- **yt-dlp** - YouTube 音訊下載
- **Demucs** - AI 人聲分離
- **Basic-pitch** - 音訊轉 MIDI
- **Music21** - 音樂理論處理
- **Spotipy** - Spotify API 整合
- **Redis** - 任務佇列管理

### 前端技術棧
- **Vanilla JavaScript** - 純 JS 實作
- **Tone.js** - Web Audio 播放
- **@tonejs/midi** - MIDI 檔案處理
- **CSS Grid/Flexbox** - 響應式佈局

### 部署架構
- **OCI ARM A1** - 免費雲端運算 (後端)
- **Cloudflare Pages** - 前端託管
- **Kaggle GPU** - AI 模型推理
- **GitHub Actions** - CI/CD 自動化
- **Docker** - 容器化部署

## 🎯 難度分級邏輯

### Easy 簡易版
- 移調到 EWI 友善調性（C/G/D/A/F/Bb）
- 簡化複雜節奏
- 移除裝飾音和複雜和弦
- 限制音域（C4-C6）
- 加入換氣記號

### Normal 標準版
- 保持原始旋律特色
- 適度簡化過於複雜的部分
- 加入基本運指提示
- 較寬鬆的音域限制

### Hard 困難版
- 保持原調挑戰性
- 加入 EWI 專屬技巧標記
- 詳細運指指導
- 進階換氣策略

## 📁 專案結構

```
EWI-EasyPlay-Scores/
├── backend/                 # Python 後端
│   ├── main.py             # FastAPI 主服務
│   ├── audio_processor.py  # 音訊處理
│   ├── midi_generator.py   # MIDI 生成
│   ├── difficulty_engine.py # 難度分級
│   ├── spotify_integration.py # Spotify 整合
│   └── requirements.txt
├── frontend/               # 前端網站
│   ├── index.html
│   ├── src/
│   │   ├── main.js
│   │   └── style.css
│   └── package.json
├── docker/                 # 容器化
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── scripts/                # 自動化腳本
│   └── deployment/
│       ├── deploy-local.sh
│       └── deploy-to-oci.sh
├── .github/workflows/      # GitHub Actions
│   ├── deploy.yml
│   └── quality.yml
└── docs/                   # 文件
    ├── API.md
    └── SETUP.md
```

## 🔧 API 端點

### 核心功能
- `POST /api/process` - 處理 YouTube 連結
- `POST /api/spotify/record-and-process` - Spotify 錄製轉譜
- `GET /api/status/{task_id}` - 查詢任務狀態
- `GET /api/download/{task_id}/{file_name}` - 下載檔案

### Spotify 整合
- `GET /api/spotify/auth` - Spotify 認證
- `GET /api/spotify/search` - 搜尋音樂
- `GET /api/spotify/callback` - OAuth 回調

### 系統監控
- `GET /health` - 健康檢查
- `GET /api/stats` - 系統統計

詳細 API 文件請參考：[API.md](docs/API.md)

## 🤝 貢獻指南

我們歡迎任何形式的貢獻！

### 如何貢獻
1. Fork 這個專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 貢獻類型
- 🐛 Bug 修復
- ✨ 新功能開發
- 📝 文件改善
- 🎨 UI/UX 優化
- 🔧 效能優化
- 🌐 多語言支援

詳細指南請參考：[CONTRIBUTING.md](CONTRIBUTING.md)

## 📋 開發路線圖

### v1.0 ✅ 已完成
- [x] YouTube 轉譜功能
- [x] 三版本難度分級
- [x] 互動練習模式
- [x] EWI 運指提示
- [x] Spotify 整合
- [x] Docker 部署

### v1.1 🚧 進行中
- [ ] 歌詞同步顯示
- [ ] 單段重複練習
- [ ] 更多 EWI 技巧標記
- [ ] 行動裝置優化
- [ ] 使用者帳號系統

### v1.2 📅 計劃中
- [ ] 多語言支援
- [ ] 練習進度追蹤
- [ ] 社群分享功能
- [ ] AI 個人化推薦
- [ ] 即時演奏評分

### v2.0 🔮 未來
- [ ] 多樂器支援
- [ ] 協作練習模式
- [ ] 音樂教學功能
- [ ] 專業版功能

## 🐛 已知問題

- 某些複雜編曲的轉譜準確度有待提升
- 極長音樂（>10分鐘）處理時間較久
- 部分非標準調性的轉調效果需優化
- Spotify 錄製功能需要 Premium 帳號

## 📊 系統需求

### 最低需求
- **CPU**: 2 核心
- **記憶體**: 4GB RAM
- **儲存**: 10GB 可用空間
- **網路**: 穩定網際網路連線

### 推薦需求
- **CPU**: 4+ 核心
- **記憶體**: 8GB+ RAM
- **儲存**: SSD 硬碟
- **GPU**: NVIDIA GPU (可選，用於加速)

## 🔐 隱私與安全

- **資料保護**: 不儲存使用者音訊檔案
- **自動清理**: 24小時後自動刪除臨時檔案
- **版權合規**: 僅處理公有領域或授權內容
- **使用限制**: 每日處理次數限制
- **安全傳輸**: 全程 HTTPS 加密

## 📄 授權條款

本專案採用 [MIT License](LICENSE) 授權。

這意味著你可以：
- ✅ 商業使用
- ✅ 修改程式碼
- ✅ 分發程式碼
- ✅ 私人使用

唯一要求：保留原始授權聲明。

## 🙏 致謝

感謝以下開源專案的支持：

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube 下載工具
- [Demucs](https://github.com/facebookresearch/demucs) - 音源分離
- [Basic-pitch](https://github.com/spotify/basic-pitch) - 音訊轉 MIDI
- [Music21](https://github.com/cuthbertLab/music21) - 音樂理論處理
- [Tone.js](https://github.com/Tonejs/Tone.js) - Web Audio 框架
- [FastAPI](https://github.com/tiangolo/fastapi) - 現代 Python Web 框架
- [Spotipy](https://github.com/spotipy-dev/spotipy) - Spotify API 客戶端

## 📞 聯絡方式

- 🐛 **Bug 回報**: [GitHub Issues](https://github.com/Paul720810/EWI-EasyPlay-Scores/issues)
- 💡 **功能建議**: [GitHub Discussions](https://github.com/Paul720810/EWI-EasyPlay-Scores/discussions)
- 📧 **Email**: paul720810@gmail.com
- 🌐 **網站**: [https://paul720810.dpdns.org](https://paul720810.dpdns.org)

## ⭐ 支持專案

如果這個專案對你有幫助，請給我們一個 ⭐ Star！

你也可以：
- 🔄 分享給其他 EWI 玩家
- 📝 撰寫使用心得
- 🤝 參與開發貢獻
- 💰 贊助專案發展

## 📈 專案統計

![GitHub stars](https://img.shields.io/github/stars/Paul720810/EWI-EasyPlay-Scores?style=social)
![GitHub forks](https://img.shields.io/github/forks/Paul720810/EWI-EasyPlay-Scores?style=social)
![GitHub issues](https://img.shields.io/github/issues/Paul720810/EWI-EasyPlay-Scores)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Paul720810/EWI-EasyPlay-Scores)

---

**讓每個 EWI 玩家都能輕鬆享受音樂練習的樂趣！** 🎵

*Made with ❤️ by the EWI community*
