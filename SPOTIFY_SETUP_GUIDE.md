# 🎵 Spotify API 設定指南

## ✅ 重要說明：Spotify API 完全免費！

**你不需要 Spotify Premium 訂閱來使用 Spotify API**
- ✅ 免費 Spotify 帳號就可以申請 Developer 帳號
- ✅ Spotify Web API 本身完全免費
- ✅ 我們只需要搜尋和基本資訊功能，免費額度完全夠用

## 🚀 5 分鐘快速設定

### 步驟 1：申請 Spotify Developer 帳號

1. **前往 Spotify Developer Dashboard**
   ```
   https://developer.spotify.com/dashboard
   ```

2. **登入你的 Spotify 帳號**
   - 使用你現有的免費 Spotify 帳號即可
   - 如果沒有帳號，先註冊一個免費帳號

3. **接受開發者條款**
   - 閱讀並接受 Spotify Developer Terms of Service
   - 這是標準流程，完全免費

### 步驟 2：創建應用程式

1. **點擊 "Create App" 按鈕**

2. **填寫應用程式資訊**：
   ```
   App name: EWI EasyPlay Scores
   App description: 智能多版本互動簡譜神器，專為 EWI 玩家設計
   Website: https://ewi.paul720810.dpdns.org
   Redirect URI: https://ewi.paul720810.dpdns.org/api/spotify/callback
   ```

3. **選擇 API 類型**：
   - ✅ 勾選 "Web API"
   - ✅ 勾選 "Web Playback SDK" (可選)

4. **同意條款並創建**

### 步驟 3：獲取 API 金鑰

創建成功後，你會看到：

```
Client ID: 一串字母數字組合 (例如: 1a2b3c4d5e6f7g8h9i0j)
Client Secret: 另一串字母數字組合 (點擊 "Show Client Secret" 顯示)
```

**⚠️ 重要**：Client Secret 是敏感資訊，不要公開分享！

### 步驟 4：配置環境變數

1. **複製環境變數範本**：
   ```bash
   cd EWI-EasyPlay-Scores
   cp .env.example .env
   ```

2. **編輯 .env 文件**：
   ```bash
   # 填入你剛獲取的 Spotify API 金鑰
   SPOTIFY_CLIENT_ID=你的_Client_ID
   SPOTIFY_CLIENT_SECRET=你的_Client_Secret
   SPOTIFY_REDIRECT_URI=https://ewi.paul720810.dpdns.org/api/spotify/callback
   ```

## 🌐 網域配置建議

### 推薦方案：使用子網域

由於你的主網域 `paul720810.dpdns.org` 已經用於 AI Agent Platform，建議使用子網域：

```
主網站: https://paul720810.dpdns.org (AI Agent Platform)
EWI 專案: https://ewi.paul720810.dpdns.org (EWI EasyPlay Scores)
```

### Cloudflare 子網域設定

1. **登入 Cloudflare Dashboard**
   ```
   https://dash.cloudflare.com
   ```

2. **選擇你的網域** `paul720810.dpdns.org`

3. **添加 DNS 記錄**：
   ```
   Type: CNAME
   Name: ewi
   Target: paul720810.dpdns.org
   Proxy status: Proxied (橘色雲朵)
   ```

4. **等待 DNS 生效** (通常 1-5 分鐘)

### 本地開發配置

在開發階段，你可以使用 localhost：

```bash
# 本地開發時的 .env 設定
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/spotify/callback
DOMAIN_NAME=localhost
```

## 🔧 測試 Spotify 整合

### 1. 啟動本地服務

```bash
cd EWI-EasyPlay-Scores
./scripts/deployment/deploy-local.sh
```

### 2. 測試 Spotify 認證

1. 訪問：`http://localhost:8000/api/spotify/auth`
2. 應該會重定向到 Spotify 登入頁面
3. 授權後會回到你的應用程式

### 3. 測試音樂搜尋

```bash
# 測試 API 端點
curl "http://localhost:8000/api/spotify/search?q=周杰倫"
```

## 📊 Spotify API 限制說明

### 免費額度 (對個人使用完全足夠)

- **搜尋請求**: 每秒 100 次
- **每日總請求**: 無明確限制，但有合理使用政策
- **並發用戶**: 25 個 (開發模式)

### 如果需要更多額度

- **申請 Extended Quota**: 免費申請更高額度
- **商業使用**: 如果日後商業化，需要申請商業許可

## 🚨 常見問題

### Q: 我的 Spotify 是免費帳號，可以申請 API 嗎？
**A**: ✅ 可以！Spotify API 與你的訂閱類型無關。

### Q: 使用 Spotify API 會產生費用嗎？
**A**: ❌ 不會！Spotify Web API 完全免費。

### Q: 我需要 Premium 才能錄製音樂嗎？
**A**: ❌ 不需要！我們的錄製功能是在瀏覽器端進行，與 Spotify 訂閱無關。

### Q: API 金鑰會過期嗎？
**A**: ❌ 不會！Client ID 和 Client Secret 是永久有效的。

### Q: 如果超過 API 限制怎麼辦？
**A**: 對於個人使用，基本不會超過。如果真的超過，可以申請更高額度。

## 🎯 下一步

1. ✅ **申請 Spotify API** (5 分鐘)
2. ✅ **配置 .env 文件** (2 分鐘)
3. ✅ **設定子網域** (5 分鐘)
4. ✅ **測試本地部署** (3 分鐘)
5. ✅ **部署到雲端** (10 分鐘)

**總計時間：約 25 分鐘就能完成整個設定！**

---

**需要幫助？**
- 📧 Email: paul720810@gmail.com
- 🐛 GitHub Issues: https://github.com/Paul720810/EWI-EasyPlay-Scores/issues
- 📚 Spotify API 文件: https://developer.spotify.com/documentation/web-api