# 忘記密碼功能使用指南

## 📧 功能概述

本系統實作了完整的「忘記密碼」功能，使用 Gmail SMTP 發送密碼重設郵件。

### 主要特色

- ✅ 使用 Gmail 官方 SMTP 服務
- ✅ 美觀的 HTML 郵件模板
- ✅ 安全的一次性重設 token
- ✅ Token 自動過期機制（預設 30 分鐘）
- ✅ 密碼強度驗證
- ✅ 防止郵箱枚舉攻擊

---

## 🔧 Gmail SMTP 設定

### 步驟 1: 啟用 Google 兩步驟驗證

1. 前往 [Google 帳戶安全性設定](https://myaccount.google.com/security)
2. 找到「登入 Google」區塊
3. 點擊「兩步驟驗證」
4. 按照指示啟用兩步驟驗證

### 步驟 2: 生成應用程式密碼

1. 在 [Google 帳戶安全性設定](https://myaccount.google.com/security) 頁面
2. 找到「登入 Google」區塊
3. 點擊「應用程式密碼」
4. 選擇「其他（自訂名稱）」
5. 輸入名稱（例如：「Accounting System」）
6. 點擊「產生」
7. **複製顯示的 16 位密碼**（例如：`abcd efgh ijkl mnop`）

⚠️ **重要**：這個密碼只會顯示一次，請立即複製！

### 步驟 3: 更新環境變數

編輯您的 `.env` 檔案：

```bash
# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com           # ← 您的 Gmail 郵箱
SMTP_PASSWORD=abcd efgh ijkl mnop            # ← 剛才生成的應用程式密碼（移除空格）
SMTP_FROM_EMAIL=your-email@gmail.com         # ← 寄件人郵箱
SMTP_FROM_NAME=Accounting System             # ← 寄件人名稱

# 密碼重設連結設定
FRONTEND_URL=http://localhost                # ← 本地開發用
# FRONTEND_URL=https://accounting.yshongcode.com  # ← 生產環境用

# Token 有效期限（分鐘）
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
```

#### 密碼格式說明

Google 生成的應用程式密碼是 **16 個字元**，顯示時會用空格分隔成 4 組，例如：

```
顯示格式: abcd efgh ijkl mnop
實際使用: abcdefghijklmnop  ← 移除所有空格
```

在 `.env` 檔案中，可以保留空格或移除，兩者都可以正常運作。

### 步驟 4: 重啟服務

```bash
docker-compose down
docker-compose up -d --build
```

---

## 🎯 使用流程

### 用戶端流程

#### 1. 請求重設密碼

1. 前往登入頁面
2. 點擊「忘記密碼？」連結
3. 輸入註冊時使用的郵箱
4. 點擊「發送重設連結」

#### 2. 檢查郵件

- 系統會發送一封包含重設連結的郵件
- 郵件主旨：「密碼重設請求 - Accounting System」
- 如果沒收到，請檢查垃圾郵件夾

#### 3. 重設密碼

1. 點擊郵件中的「重設密碼」按鈕
2. 輸入新密碼（需符合強度要求）
3. 確認新密碼
4. 點擊「確認重設密碼」

#### 4. 使用新密碼登入

重設成功後，使用新密碼登入系統。

---

## 🔐 安全特性

### 1. 防止郵箱枚舉

無論郵箱是否存在，系統都返回相同訊息：
```
如果該郵箱已註冊，您將收到密碼重設郵件
```

這防止攻擊者探測系統中的有效郵箱。

### 2. Token 安全性

- 使用 `secrets.token_urlsafe(32)` 生成隨機 token
- Token 長度 43 字元，熵值極高
- 每個 token 只能使用一次
- Token 自動過期（預設 30 分鐘）

### 3. 密碼強度驗證

新密碼必須符合以下要求：
- ✅ 至少 8 個字元
- ✅ 至少 1 個大寫字母 (A-Z)
- ✅ 至少 1 個小寫字母 (a-z)
- ✅ 至少 1 個數字 (0-9)
- ✅ 至少 1 個特殊字元 (!@#$%^&*(),.?":{}|<>)

### 4. Token 驗證流程

```
1. 用戶點擊郵件連結
2. 前端驗證 token 是否存在
3. 後端檢查 token:
   - 是否存在於資料庫
   - 是否已被使用
   - 是否已過期
4. 驗證通過後允許設定新密碼
5. 更新密碼後標記 token 為已使用
```

---

## 📊 資料庫結構

### PasswordResetToken 資料表

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | Integer | 主鍵 |
| email | String | 用戶郵箱 |
| token | String | 重設 token（唯一） |
| is_used | Boolean | 是否已使用 |
| created_at | DateTime | 建立時間 |
| expires_at | DateTime | 過期時間 |

### 自動清理

建議定期清理過期的 token：

```sql
DELETE FROM password_reset_tokens
WHERE expires_at < NOW() OR is_used = true;
```

---

## 🌐 API Endpoints

### 1. 請求密碼重設

```http
POST /api/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "如果該郵箱已註冊，您將收到密碼重設郵件"
}
```

### 2. 驗證 Token

```http
GET /api/password-reset/verify-token/{token}
```

**Response:**
```json
{
  "valid": true,
  "message": "連結有效"
}
```

### 3. 確認重設密碼

```http
POST /api/password-reset/confirm
Content-Type: application/json

{
  "token": "abc123...",
  "new_password": "NewPassword123!"
}
```

**Response:**
```json
{
  "message": "密碼已成功重設，請使用新密碼登入"
}
```

---

## 🎨 郵件模板

郵件使用精美的 HTML 模板，包含：

- 🎨 深色主題，符合系統風格
- 🔵 Cyan 主色調 (#00d4ff)
- 📱 響應式設計
- ✨ 漸層背景和陰影效果
- ⚠️ 清晰的安全提醒
- 📌 重要資訊高亮顯示

---

## ⚠️ 常見問題

### Q1: 沒收到重設郵件？

**可能原因：**
1. 郵箱填寫錯誤
2. Gmail SMTP 設定錯誤
3. 郵件進入垃圾郵件夾
4. 應用程式密碼錯誤

**解決方法：**
```bash
# 檢查 Docker 容器日誌
docker-compose logs backend | grep email

# 檢查 SMTP 設定
docker-compose exec backend python -c "from app.core.config import settings; print(f'SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}, User: {settings.SMTP_USERNAME}')"
```

### Q2: Token 過期太快？

編輯 `.env` 調整過期時間：
```bash
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=60  # 改為 60 分鐘
```

### Q3: 如何測試郵件發送？

使用 Python 腳本測試：

```python
# test_email.py
from app.core.email import send_password_reset_email

# 發送測試郵件
success = send_password_reset_email(
    to_email="your-test@email.com",
    reset_token="test-token-12345"
)

print(f"Email sent: {success}")
```

```bash
# 在 backend 容器中執行
docker-compose exec backend python test_email.py
```

### Q4: Gmail 拒絕連線？

**錯誤訊息：**
```
SMTPAuthenticationError: Username and Password not accepted
```

**解決方法：**
1. 確認已啟用兩步驟驗證
2. 重新生成應用程式密碼
3. 確認密碼無誤（移除空格）
4. 檢查是否被 Gmail 封鎖

### Q5: 如何更改郵件主旨或內容？

編輯 `backend/app/core/email.py` 中的 `send_password_reset_email()` 函數。

---

## 🚀 部署到生產環境

### 更新生產環境 .env

```bash
# 生產環境設定
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-production-email@gmail.com
SMTP_PASSWORD=your-production-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com  # 可使用自訂域名郵箱
SMTP_FROM_NAME=Accounting System

# 重要：使用 HTTPS 網域
FRONTEND_URL=https://accounting.yshongcode.com

PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
```

### 重新部署

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📝 維護建議

### 定期清理過期 Token

建議每天清理一次過期的 token：

```bash
# 連接到資料庫
docker-compose exec db psql -U accounting_user -d accounting_db

# 清理過期 token
DELETE FROM password_reset_tokens WHERE expires_at < NOW();

# 清理已使用的 token（7 天前）
DELETE FROM password_reset_tokens
WHERE is_used = true AND created_at < NOW() - INTERVAL '7 days';
```

### 監控郵件發送

```bash
# 查看郵件發送日誌
docker-compose logs backend | grep "Email sent"
docker-compose logs backend | grep "Failed to send email"
```

---

## 🔗 相關連結

- [Gmail SMTP 設定](https://support.google.com/accounts/answer/185833)
- [Google 應用程式密碼](https://myaccount.google.com/apppasswords)
- [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/)

---

**最後更新**: 2025-11-26
**版本**: 1.0.0
