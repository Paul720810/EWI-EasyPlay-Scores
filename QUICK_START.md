# 🚀 EWI EasyPlay Scores 快速開始

## 📋 總結回答你的問題

### 🌐 網域使用建議
**✅ 推薦：使用子網域，不會影響現有網站**

```
現有 AI 平台: https://paul720810.dpdns.org
EWI 專案: https://ewi.paul720810.dpdns.org
```

**優點**：
- ✅ 不影響你現有的 AI Agent Platform
- ✅ 同一網域下的不同服務
- ✅ 管理方便，SEO 友善
- ✅ 可以同時運行兩個網站

### 🎵 Spotify API 費用
**✅ 完全免費！你的免費 Spotify 帳號就可以申請**

- ✅ Spotify Web API 本身免費
- ✅ 免費 Spotify 帳號可申請 Developer 帳號
- ✅ 我們只需要搜尋功能，免費額度完全夠用
- ✅ 不需要 Premium 訂閱

## ⚡ 3 步驟快速部署

### 步驟 1：申請 Spotify API (5 分鐘)
```bash
1. 前往: https://developer.spotify.com/dashboard
2. 用你的免費 Spotify 帳號登入
3. 創建應用程式:
   - App name: EWI EasyPlay Scores
   - Redirect URI: https://ewi.paul720810.dpdns.org/api/spotify/callback
4. 獲取 Client ID 和 Client Secret
```

### 步驟 2：配置環境 (2 分鐘)
```bash
cd EWI-EasyPlay-Scores
cp .env.example .env

# 編輯 .env 文件，填入:
SPOTIFY_CLIENT_ID=你的_Client_ID
SPOTIFY_CLIENT_SECRET=你的_Client_Secret
```

### 步驟 3：一鍵部署 (3 分鐘)
```bash
# 本地測試
./scripts/deployment/deploy-local.sh

# 訪問: http://localhost
# API 文件: http://localhost:8000/docs
```

## 🌐 Cloudflare 子網域設定

### 在 Cloudflare Dashboard 添加 DNS 記錄：
```
Type: CNAME
Name: ewi
Target: paul720810.dpdns.org
Proxy: 開啟 (橘色雲朵)
```

### 等待 DNS 生效後，你就有兩個網站：
```
AI 平台: https://paul720810.dpdns.org
EWI 工具: https://ewi.paul720810.dpdns.org
```

## 🎯 功能測試清單

### ✅ YouTube 轉譜測試
1. 貼上 YouTube 音樂連結
2. 點擊「開始轉譜」
3. 等待處理完成 (約 2-3 分鐘)
4. 下載 Easy/Normal/Hard 三個版本

### ✅ Spotify 錄製測試
1. 點擊「連接 Spotify」
2. 完成 OAuth 認證
3. 搜尋想要的音樂
4. 選擇錄製時長 (10-180 秒)
5. 點擊「錄製並轉譜」

## 📊 預期效果

### 🎵 轉譜品質
- **Easy 版本**: 簡化節奏，EWI 友善調性
- **Normal 版本**: 保持原曲特色，適度簡化
- **Hard 版本**: 挑戰性版本，詳細運指指導

### ⚡ 處理速度
- **YouTube**: 2-5 分鐘 (取決於歌曲長度)
- **Spotify 錄製**: 錄製時長 + 1-2 分鐘處理

### 🎹 EWI 優化
- 自動調性轉換 (C/G/D/A/F/Bb)
- 運指提示和換氣記號
- 音域限制 (C4-C6 for Easy)

## 🚨 如果遇到問題

### Spotify 認證失敗
```bash
# 檢查 .env 配置
cat .env | grep SPOTIFY

# 確認 Redirect URI 設定正確
# 應該是: https://ewi.paul720810.dpdns.org/api/spotify/callback
```

### Docker 啟動失敗
```bash
# 檢查日誌
docker-compose logs backend
docker-compose logs frontend

# 重新建置
docker-compose down
docker-compose up --build -d
```

### 網域無法訪問
```bash
# 檢查 DNS 設定
nslookup ewi.paul720810.dpdns.org

# 確認 Cloudflare Proxy 已開啟
```

## 🎉 成功指標

當你看到以下畫面，表示部署成功：

1. **前端頁面** (`http://localhost` 或 `https://ewi.paul720810.dpdns.org`)
   - 看到 EWI EasyPlay Scores 標題
   - YouTube 和 Spotify 兩個選項卡
   - 可以輸入 YouTube 連結

2. **API 文件** (`http://localhost:8000/docs`)
   - 看到 FastAPI 自動生成的 API 文件
   - 可以測試各個 API 端點

3. **Spotify 整合**
   - 點擊「連接 Spotify」能跳轉到 Spotify 登入頁面
   - 授權後能成功返回並搜尋音樂

## 📞 需要幫助？

- 🐛 **技術問題**: [GitHub Issues](https://github.com/Paul720810/EWI-EasyPlay-Scores/issues)
- 📧 **Email**: paul720810@gmail.com
- 📚 **詳細文件**: 
  - [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
  - [SPOTIFY_SETUP_GUIDE.md](SPOTIFY_SETUP_GUIDE.md)

---

**🎵 準備好享受 EWI 練習的樂趣了嗎？開始你的音樂之旅吧！** 🎶✨