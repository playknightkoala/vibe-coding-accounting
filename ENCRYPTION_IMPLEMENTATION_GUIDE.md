# 混合加密方案實作指南

## 概述

本專案使用混合加密方案來保護交易敏感資料（description、note、description_history）：
- **標準註冊用戶**：使用從用戶密碼派生的專屬加密金鑰（最高安全性）
- **Google OAuth 用戶**：使用系統主金鑰加密（中等安全性）

---

## 當前狀態

### 已完成的部分：
✅ 基礎加密模組（`backend/app/core/encryption.py`）
  - `encrypt_field()` 和 `decrypt_field()` 使用系統主金鑰
  - 支援向後相容（舊資料未加密仍可讀取）

✅ Transaction Model 加密
  - `description` 和 `note` 欄位使用 `@hybrid_property` 自動加密/解密
  - 使用 `_description` 和 `_note` 儲存加密資料

✅ DescriptionHistory Model 加密
  - `description` 欄位使用 `@hybrid_property` 自動加密/解密
  - 使用 `_description` 儲存加密資料

### 需要實作的部分：
❌ User Model 新增欄位（`encryption_salt`, `use_password_encryption`）
❌ 註冊流程改造（生成 salt）
❌ 登入流程改造（派生金鑰並放入 JWT）
❌ 加密模組擴充（支援密碼派生金鑰）
❌ Transaction/DescriptionHistory Model 改造（支援雙模式）
❌ Google 用戶設定密碼功能（可選）
❌ 密碼變更功能（重新加密資料）

---

## 資料庫架構變更

### 1. User Model 新增欄位

**檔案位置**: `backend/app/models/user.py`

```python
from sqlalchemy import Column, String, Boolean

class User(Base):
    __tablename__ = "users"

    # ... 現有欄位 ...

    # 新增欄位
    encryption_salt = Column(String, nullable=True)
    """用戶專屬的加密 salt，僅用於標準註冊用戶"""

    use_password_encryption = Column(Boolean, default=False, nullable=False)
    """是否使用密碼派生加密金鑰（True=標準用戶, False=Google用戶）"""
```

**資料庫遷移**（如果使用 Alembic）：
```sql
ALTER TABLE users ADD COLUMN encryption_salt VARCHAR;
ALTER TABLE users ADD COLUMN use_password_encryption BOOLEAN DEFAULT FALSE NOT NULL;
```

**手動更新現有用戶**（首次部署）：
```sql
-- 標記現有標準用戶為使用系統金鑰（維持現狀）
UPDATE users SET use_password_encryption = FALSE WHERE is_google_user = FALSE;

-- Google 用戶已經是 FALSE，無需更新
UPDATE users SET use_password_encryption = FALSE WHERE is_google_user = TRUE;
```

---

## 實作步驟

### 步驟 1：擴充加密模組

**檔案位置**: `backend/app/core/encryption.py`

**在現有代碼後新增以下函數**：

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
from typing import Optional

# ===== 用戶專屬金鑰派生 =====

def derive_user_encryption_key(password: str, salt: str) -> bytes:
    """
    從用戶密碼和 salt 派生加密金鑰

    Args:
        password: 用戶的明文密碼（僅在登入時可用）
        salt: 用戶專屬的 salt（儲存在資料庫）

    Returns:
        Fernet 可用的 32-byte 金鑰
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode('utf-8'),
        iterations=100000,  # 高迭代次數增加破解難度
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return key


def get_user_encryption_key(user, password: str = None) -> bytes:
    """
    根據用戶類型返回對應的加密金鑰

    Args:
        user: User 物件
        password: 明文密碼（僅標準登入用戶需要）

    Returns:
        加密金鑰

    Raises:
        ValueError: 當密碼派生用戶缺少密碼時
    """
    if user.use_password_encryption:
        # 方案 2：從密碼派生金鑰
        if not password and not hasattr(user, '_encryption_key'):
            raise ValueError("需要密碼才能解密此用戶的資料")

        if hasattr(user, '_encryption_key'):
            return user._encryption_key

        return derive_user_encryption_key(password, user.encryption_salt)
    else:
        # 方案 1：使用系統主金鑰
        return _get_encryption_key()


def encrypt_field_with_key(text: Optional[str], encryption_key: bytes) -> Optional[str]:
    """
    使用指定金鑰加密文字

    Args:
        text: 要加密的文字
        encryption_key: Fernet 金鑰

    Returns:
        加密後的文字
    """
    if not text:
        return text

    try:
        f = Fernet(encryption_key)
        encrypted_bytes = f.encrypt(text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Field encryption error: {e}")
        return text


def decrypt_field_with_key(encrypted_text: Optional[str], encryption_key: bytes) -> Optional[str]:
    """
    使用指定金鑰解密文字

    Args:
        encrypted_text: 加密的文字
        encryption_key: Fernet 金鑰

    Returns:
        解密後的文字
    """
    if not encrypted_text:
        return encrypted_text

    try:
        f = Fernet(encryption_key)
        decrypted_bytes = f.decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # 解密失敗，返回原文（向後相容）
        return encrypted_text
```

---

### 步驟 2：修改註冊流程

**檔案位置**: `backend/app/api/auth.py`

**找到 `/register` 端點，修改如下**：

```python
import secrets
from app.core.security import get_password_hash

@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 檢查用戶名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用戶名已存在")

    # 對密碼進行 hash
    hashed_password = get_password_hash(user_data.password)

    # 生成用戶專屬的加密 salt（64 字元 hex）
    user_salt = secrets.token_hex(32)

    # 創建新用戶
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        encryption_salt=user_salt,
        use_password_encryption=True,  # 標準註冊用戶啟用密碼派生加密
        is_google_user=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "註冊成功", "username": new_user.username}
```

---

### 步驟 3：修改登入流程

**檔案位置**: `backend/app/api/auth.py`

**找到 `/login` 端點，修改如下**：

```python
import base64
from app.core.encryption import derive_user_encryption_key
from app.core.security import create_access_token

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 驗證用戶名和密碼
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 根據用戶類型生成 token 資料
    token_data = {"sub": user.username}

    if user.use_password_encryption:
        # 標準用戶：派生加密金鑰並放入 token
        encryption_key = derive_user_encryption_key(
            password=form_data.password,
            salt=user.encryption_salt
        )
        encryption_key_b64 = base64.b64encode(encryption_key).decode('utf-8')
        token_data["encryption_key"] = encryption_key_b64
    else:
        # Google 用戶：不需要攜帶金鑰
        token_data["encryption_key"] = None

    token_data["use_password_encryption"] = user.use_password_encryption

    # 如果用戶啟用 2FA，返回 requires_2fa
    if user.two_factor_enabled:
        return {"access_token": "", "token_type": "bearer", "requires_2fa": True}

    # 創建 JWT token
    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}
```

---

### 步驟 4：修改 Google OAuth 登入流程

**檔案位置**: `backend/app/api/auth.py`

**找到 `/auth/google/callback` 端點，修改如下**：

```python
@router.get("/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    # ... 現有的 Google OAuth 驗證邏輯 ...

    # 獲取 Google 用戶資訊
    user_info = await oauth.google.authorize_access_token(code)
    email = user_info.get('email')

    # 查找或創建用戶
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # 創建新的 Google 用戶
        user = User(
            username=email,
            email=email,
            is_google_user=True,
            use_password_encryption=False,  # Google 用戶使用系統金鑰
            encryption_salt=None  # 不需要 salt
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 為新用戶創建默認帳戶...

    # 創建 token（Google 用戶不需要 encryption_key）
    access_token = create_access_token(
        data={
            "sub": user.username,
            "encryption_key": None,
            "use_password_encryption": False
        }
    )

    # 重定向到前端並帶上 token
    redirect_url = f"{settings.FRONTEND_URL}/google-callback?token={access_token}"
    return RedirectResponse(url=redirect_url)
```

---

### 步驟 5：修改依賴注入（獲取當前用戶）

**檔案位置**: `backend/app/api/deps.py`

**找到 `get_current_user` 函數，修改如下**：

```python
import base64
from jose import JWTError, jwt
from app.core.config import settings

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解碼 JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        encryption_key_b64: str = payload.get("encryption_key")
        use_password_encryption: bool = payload.get("use_password_encryption", False)

        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 從資料庫獲取用戶
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    # 如果是密碼派生加密用戶，將金鑰附加到 user 物件
    if use_password_encryption and encryption_key_b64:
        user._encryption_key = base64.b64decode(encryption_key_b64)

    return user
```

---

### 步驟 6：修改 Transaction Model

**檔案位置**: `backend/app/models/transaction.py`

**替換現有的 `@hybrid_property` 實作**：

```python
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.encryption import encrypt_field, decrypt_field, encrypt_field_with_key, decrypt_field_with_key

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    _description = Column("description", String, nullable=False)
    _note = Column("note", String, nullable=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)
    category = Column(String)
    # ... 其他欄位 ...

    account = relationship("Account", back_populates="transactions")

    @hybrid_property
    def description(self):
        """解密 description（自動判斷用戶類型）"""
        user = self.account.owner

        if user.use_password_encryption:
            # 密碼派生用戶：使用用戶專屬金鑰
            if hasattr(user, '_encryption_key'):
                return decrypt_field_with_key(self._description, user._encryption_key)
            else:
                return "[需要密碼解鎖]"
        else:
            # Google 用戶：使用系統金鑰
            return decrypt_field(self._description)

    @description.setter
    def description(self, value):
        """加密 description"""
        user = self.account.owner

        if user.use_password_encryption:
            if hasattr(user, '_encryption_key'):
                self._description = encrypt_field_with_key(value, user._encryption_key)
            else:
                raise ValueError("無法加密：缺少加密金鑰")
        else:
            self._description = encrypt_field(value)

    @hybrid_property
    def note(self):
        """解密 note"""
        if not self._note:
            return None

        user = self.account.owner

        if user.use_password_encryption:
            if hasattr(user, '_encryption_key'):
                return decrypt_field_with_key(self._note, user._encryption_key)
            else:
                return "[需要密碼解鎖]"
        else:
            return decrypt_field(self._note)

    @note.setter
    def note(self, value):
        """加密 note"""
        if not value:
            self._note = None
            return

        user = self.account.owner

        if user.use_password_encryption:
            if hasattr(user, '_encryption_key'):
                self._note = encrypt_field_with_key(value, user._encryption_key)
            else:
                raise ValueError("無法加密：缺少加密金鑰")
        else:
            self._note = encrypt_field(value)
```

---

### 步驟 7：修改 DescriptionHistory Model

**檔案位置**: `backend/app/models/description_history.py`

**替換現有的 `@hybrid_property` 實作**：

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.encryption import encrypt_field, decrypt_field, encrypt_field_with_key, decrypt_field_with_key

class DescriptionHistory(Base):
    """交易敘述歷史記錄表"""
    __tablename__ = "description_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    _description = Column("description", String, nullable=False, index=True)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 添加關聯以便獲取 user
    user = relationship("User")

    @hybrid_property
    def description(self):
        """解密 description"""
        if self.user.use_password_encryption:
            if hasattr(self.user, '_encryption_key'):
                return decrypt_field_with_key(self._description, self.user._encryption_key)
            else:
                return "[需要密碼解鎖]"
        else:
            return decrypt_field(self._description)

    @description.setter
    def description(self, value):
        """加密 description"""
        if self.user.use_password_encryption:
            if hasattr(self.user, '_encryption_key'):
                self._description = encrypt_field_with_key(value, self.user._encryption_key)
            else:
                raise ValueError("無法加密：缺少加密金鑰")
        else:
            self._description = encrypt_field(value)
```

---

## 可選功能

### 功能 1：Google 用戶設定密碼（升級安全性）

**檔案位置**: `backend/app/api/users.py`

**新增端點**：

```python
import secrets
from app.core.encryption import derive_user_encryption_key, encrypt_field_with_key, decrypt_field, _get_encryption_key
from app.core.security import get_password_hash

@router.post("/me/set-password")
def set_password_for_google_user(
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Google 用戶設定密碼以升級到更高安全性
    """
    if not current_user.is_google_user:
        raise HTTPException(status_code=400, detail="僅 Google 用戶可設定密碼")

    if current_user.use_password_encryption:
        raise HTTPException(status_code=400, detail="已設定過密碼")

    # 1. 生成新的 salt 和金鑰
    new_salt = secrets.token_hex(32)
    new_key = derive_user_encryption_key(new_password, new_salt)
    old_key = _get_encryption_key()  # 系統金鑰

    # 2. 重新加密所有交易資料
    from app.models.transaction import Transaction
    from app.models.account import Account

    transactions = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id
    ).all()

    for txn in transactions:
        # 用系統金鑰解密
        description = decrypt_field_with_key(txn._description, old_key)
        note = decrypt_field_with_key(txn._note, old_key) if txn._note else None

        # 用新密碼金鑰重新加密
        txn._description = encrypt_field_with_key(description, new_key)
        if note:
            txn._note = encrypt_field_with_key(note, new_key)

    # 3. 重新加密 DescriptionHistory
    from app.models.description_history import DescriptionHistory

    histories = db.query(DescriptionHistory).filter(
        DescriptionHistory.user_id == current_user.id
    ).all()

    for history in histories:
        description = decrypt_field_with_key(history._description, old_key)
        history._description = encrypt_field_with_key(description, new_key)

    # 4. 更新用戶設定
    current_user.hashed_password = get_password_hash(new_password)
    current_user.encryption_salt = new_salt
    current_user.use_password_encryption = True

    db.commit()

    return {"message": "密碼已設定，安全性已升級至最高等級"}
```

---

### 功能 2：密碼變更（重新加密資料）

**檔案位置**: `backend/app/api/users.py`

**新增端點**：

```python
@router.post("/me/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    變更密碼並重新加密所有資料
    """
    from app.core.security import verify_password, get_password_hash
    from app.core.encryption import derive_user_encryption_key, encrypt_field_with_key, decrypt_field_with_key
    from app.models.transaction import Transaction
    from app.models.account import Account
    from app.models.description_history import DescriptionHistory

    # 1. 驗證舊密碼
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="舊密碼錯誤")

    # 2. 如果用戶不是密碼派生加密，不允許變更
    if not current_user.use_password_encryption:
        raise HTTPException(status_code=400, detail="Google 用戶請使用「設定密碼」功能")

    # 3. 派生舊金鑰和新金鑰
    old_key = derive_user_encryption_key(old_password, current_user.encryption_salt)
    new_salt = secrets.token_hex(32)
    new_key = derive_user_encryption_key(new_password, new_salt)

    # 4. 重新加密所有交易資料
    transactions = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id
    ).all()

    for txn in transactions:
        # 用舊金鑰解密
        description = decrypt_field_with_key(txn._description, old_key)
        note = decrypt_field_with_key(txn._note, old_key) if txn._note else None

        # 用新金鑰重新加密
        txn._description = encrypt_field_with_key(description, new_key)
        if note:
            txn._note = encrypt_field_with_key(note, new_key)

    # 5. 重新加密 DescriptionHistory
    histories = db.query(DescriptionHistory).filter(
        DescriptionHistory.user_id == current_user.id
    ).all()

    for history in histories:
        description = decrypt_field_with_key(history._description, old_key)
        history._description = encrypt_field_with_key(description, new_key)

    # 6. 更新用戶密碼和 salt
    current_user.hashed_password = get_password_hash(new_password)
    current_user.encryption_salt = new_salt

    db.commit()

    return {"message": "密碼已更新，所有資料已重新加密"}
```

---

## 部署檢查清單

### 首次部署（升級現有系統）

1. ✅ **備份資料庫**
   ```bash
   docker-compose exec db pg_dump -U accounting_user accounting_db > backup.sql
   ```

2. ✅ **執行資料庫遷移**
   ```sql
   ALTER TABLE users ADD COLUMN encryption_salt VARCHAR;
   ALTER TABLE users ADD COLUMN use_password_encryption BOOLEAN DEFAULT FALSE NOT NULL;

   -- 將現有用戶設為使用系統金鑰（維持現狀，不破壞現有資料）
   UPDATE users SET use_password_encryption = FALSE;
   ```

3. ✅ **部署新代碼**
   ```bash
   git pull
   docker-compose build backend
   docker-compose restart backend
   ```

4. ✅ **驗證功能**
   - 現有用戶登入：應正常解密顯示資料（使用系統金鑰）
   - 新註冊用戶：自動啟用密碼派生加密
   - Google 用戶：繼續使用系統金鑰

---

## 安全性對比

| 用戶類型 | 加密方式 | 金鑰來源 | 安全等級 | 密碼遺失後果 |
|---------|---------|---------|---------|------------|
| **新註冊用戶** | 密碼派生金鑰 | `PBKDF2(password + salt)` | ⭐⭐⭐⭐⭐ | 資料永久遺失 |
| **Google 用戶** | 系統主金鑰 | `DATA_ENCRYPTION_KEY` | ⭐⭐⭐ | 可找回 |
| **舊用戶（遷移前）** | 系統主金鑰 | `DATA_ENCRYPTION_KEY` | ⭐⭐⭐ | 可找回 |

---

## 常見問題

### Q1: 現有用戶的資料會受影響嗎？
**A**: 不會。現有用戶會標記為 `use_password_encryption=False`，繼續使用系統金鑰，資料完全不受影響。

### Q2: 用戶忘記密碼怎麼辦？
**A**:
- **Google 用戶**：資料可找回（使用系統金鑰）
- **密碼派生用戶**：資料永久遺失（這是最高安全性的代價）

### Q3: 可以讓現有用戶升級到密碼派生加密嗎？
**A**: 技術上可行，但需要用戶「設定新密碼」並重新加密所有資料。建議僅對新註冊用戶啟用。

### Q4: JWT token 會變大嗎？
**A**: 是的，密碼派生用戶的 token 會增加約 44 字元（base64 編碼的 32-byte 金鑰）。

### Q5: 效能影響？
**A**:
- **登入時**：PBKDF2 需要 ~100ms（100,000 次迭代）
- **API 請求**：無影響（金鑰已在 token 中）

---

## 技術細節

### 加密演算法
- **對稱加密**: Fernet (AES 128 in CBC mode)
- **金鑰派生**: PBKDF2-HMAC-SHA256 (100,000 iterations)
- **Salt 長度**: 64 字元 (32 bytes hex)
- **金鑰長度**: 32 bytes

### JWT Token 結構
```json
{
  "sub": "username",
  "encryption_key": "base64_encoded_key_or_null",
  "use_password_encryption": true_or_false,
  "exp": 1234567890
}
```

---

## 維護建議

1. **定期備份 `DATA_ENCRYPTION_KEY`**
   - 儲存在安全的密碼管理器（如 1Password, Bitwarden）
   - 不要提交到 Git

2. **監控解密失敗**
   - 在 `decrypt_field()` 中加入日誌記錄
   - 定期檢查是否有大量解密失敗

3. **金鑰輪換計畫**
   - 每年更換 `DATA_ENCRYPTION_KEY`
   - 重新加密所有 Google 用戶的資料

---

## 參考資料

- [Fernet 規範](https://github.com/fernet/spec/)
- [PBKDF2 標準](https://tools.ietf.org/html/rfc2898)
- [OWASP 資料加密指南](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

---

**文件版本**: 1.0
**最後更新**: 2025-12-04
**作者**: Claude Code
