# 生產環境部署修復說明

## 問題描述

在生產環境 (https://accounting.yshongcode.com/) 出現以下控制台錯誤:

### 錯誤 1: Cloudflare Insights 被阻擋
```
GET https://static.cloudflareinsights.com/beacon.min.js/... net::ERR_BLOCKED_BY_CLIENT
```

**原因:** 使用者的廣告阻擋器阻擋了 Cloudflare 分析腳本
**安全性:** ✅ 無安全問題
**影響:** 無法收集訪客分析數據
**解決:** 此為正常現象,無需修復

### 錯誤 2: Vite HMR WebSocket 連線失敗 ⚠️
```
WebSocket connection to 'wss://accounting.yshongcode.com/?token=...' failed
WebSocket connection to 'wss://localhost:5173/?token=...' failed
[vite] failed to connect to websocket
```

**原因:** 生產環境使用了開發模式的 Vite dev server
**安全性:** ⚠️ 輕微安全風險 - 暴露內部開發工具
**影響:**
- 控制台紅色錯誤訊息
- 不必要的 WebSocket 連線嘗試
- 看起來不專業

## 解決方案

### 修改的檔案

#### 1. `frontend/Dockerfile`

**問題:**
```dockerfile
CMD ["npm", "run", "dev"]  # ❌ 使用開發伺服器
```

**修復後:**
```dockerfile
# Build argument to determine environment
ARG NODE_ENV=development

# Build for production if NODE_ENV=production
RUN if [ "$NODE_ENV" = "production" ]; then \
      npm run build; \
    fi

# Set as environment variable for runtime
ENV NODE_ENV=${NODE_ENV}

# Run dev server in development, serve built files in production
CMD sh -c 'if [ "$NODE_ENV" = "production" ]; then \
      npx vite preview --host 0.0.0.0 --port 5173; \
    else \
      npm run dev; \
    fi'
```

**改進:**
- ✅ 根據 `NODE_ENV` 決定建置模式
- ✅ 生產環境使用 `vite preview` (提供建置後的靜態檔案)
- ✅ 開發環境使用 `npm run dev` (支援 HMR)

#### 2. `docker-compose.prod.yml`

**新增:**
```yaml
frontend:
  build:
    args:
      - NODE_ENV=production  # ✅ 建置時設定
  environment:
    - NODE_ENV=production    # ✅ 執行時設定
    - VITE_HMR_CLIENT_PORT=false  # ✅ 明確停用 HMR
```

**改進:**
- ✅ 建置時傳遞 `NODE_ENV=production`
- ✅ 執行時也設定 `NODE_ENV=production`
- ✅ 明確停用 Vite HMR

## 部署步驟

### 立即修復生產環境

在伺服器上執行:

```bash
cd ~/accounting-project-new

# 1. 拉取最新程式碼
git pull origin main

# 2. 重新建置並啟動
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d frontend

# 3. 查看日誌確認
docker-compose -f docker-compose.prod.yml logs frontend | tail -20
```

### 驗證修復

部署後,開啟瀏覽器控制台 (F12),應該:

✅ **不再出現:**
```
WebSocket connection to 'wss://...' failed
[vite] failed to connect to websocket
```

✅ **正常行為:**
- 應用程式正常載入
- 無 WebSocket 連線嘗試
- 控制台乾淨(除了可能有 Cloudflare Insights 被阻擋,這是正常的)

### 檢查前端模式

```bash
# 連接到前端容器
docker-compose -f docker-compose.prod.yml exec frontend sh

# 檢查環境變數
echo $NODE_ENV
# 應該輸出: production

# 檢查是否有 dist 目錄 (建置產物)
ls -la /app/dist
# 應該看到 index.html, assets/ 等檔案

# 退出容器
exit
```

## 開發環境 vs 生產環境對比

| 項目 | 開發環境 | 生產環境 |
|------|---------|---------|
| **Docker Compose 檔案** | `docker-compose.yml` | `docker-compose.prod.yml` |
| **NODE_ENV** | `development` | `production` |
| **前端模式** | `npm run dev` (Vite dev server) | `vite preview` (靜態檔案) |
| **HMR** | ✅ 啟用 | ❌ 停用 |
| **WebSocket** | ✅ 用於 HMR | ❌ 無 |
| **建置** | ❌ 不建置 | ✅ `npm run build` |
| **檔案** | 原始碼 | 建置產物 (`dist/`) |
| **效能** | 較慢(即時編譯) | 快速(預先建置) |
| **檔案大小** | 較大 | 最小化壓縮 |

## Vite Preview vs Dev Server

### Vite Dev Server (`npm run dev`)
- ✅ 支援 HMR (熱模組替換)
- ✅ 即時編譯
- ✅ 詳細錯誤訊息
- ❌ 效能較慢
- ❌ 需要 WebSocket
- 🎯 **適用:** 開發環境

### Vite Preview (`vite preview`)
- ✅ 提供建置後的靜態檔案
- ✅ 效能優化(壓縮、最小化)
- ✅ 無 WebSocket
- ✅ 接近真實生產環境
- ❌ 無 HMR
- 🎯 **適用:** 生產環境、預覽建置結果

## 常見問題

### Q: 為什麼之前沒有發現這個問題?

A: 因為:
1. 應用程式功能正常運作
2. 只有開啟瀏覽器控制台才會看到錯誤
3. WebSocket 連線失敗不影響核心功能

### Q: 這個錯誤會影響 SEO 嗎?

A: 不會。搜尋引擎爬蟲不會受到 JavaScript 控制台錯誤的影響。

### Q: Cloudflare Insights 錯誤需要修復嗎?

A: 不需要。這是使用者端廣告阻擋器造成的,屬於正常現象。如果需要分析數據,可以考慮:
- 使用其他分析工具 (Google Analytics, Matomo 等)
- 請求使用者停用廣告阻擋器(不推薦)
- 接受無法收集所有使用者數據的事實

### Q: 如何在本機測試生產建置?

A: 使用以下命令:

```bash
# 在 frontend 目錄
npm run build
npx vite preview

# 或使用 Docker
docker-compose -f docker-compose.prod.yml up frontend
```

## 安全性影響

### 修復前
- ⚠️ 暴露開發工具(Vite dev server)
- ⚠️ 控制台錯誤可能讓使用者不信任網站
- ⚠️ 增加不必要的網路請求

### 修復後
- ✅ 只提供靜態建置檔案
- ✅ 控制台乾淨
- ✅ 網路請求最小化
- ✅ 更專業的使用者體驗

## 總結

這次修復:
1. ✅ 移除了生產環境中的開發工具
2. ✅ 消除了 WebSocket 錯誤訊息
3. ✅ 提升了安全性
4. ✅ 改善了使用者體驗
5. ✅ 減少了不必要的網路請求

修復後,生產環境將使用正確的建置流程,不再出現 Vite HMR 相關的錯誤訊息。
