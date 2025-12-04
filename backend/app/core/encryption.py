from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from typing import Optional
from app.core.config import settings

# ===== 快取機制：避免重複計算金鑰 =====
_cached_encryption_key: Optional[bytes] = None
_cached_fernet: Optional[Fernet] = None

def _get_encryption_key() -> bytes:
    """
    從 DATA_ENCRYPTION_KEY 生成 Fernet 密鑰
    使用 PBKDF2HMAC 將密鑰派生為標準格式

    ⚡ 效能優化：金鑰會被快取，避免重複執行 PBKDF2（100,000 次迭代）
    """
    global _cached_encryption_key

    # 如果已有快取，直接返回
    if _cached_encryption_key is not None:
        return _cached_encryption_key

    # 使用固定的 salt（因為我們需要一致的密鑰）
    salt = b'accounting_app_salt_v1'

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )

    key = base64.urlsafe_b64encode(kdf.derive(settings.DATA_ENCRYPTION_KEY.encode()))

    # 快取金鑰
    _cached_encryption_key = key

    return key

def _get_fernet() -> Fernet:
    """
    取得 Fernet 加密器實例

    ⚡ 效能優化：Fernet 實例會被快取並重複使用
    """
    global _cached_fernet

    # 如果已有快取，直接返回
    if _cached_fernet is not None:
        return _cached_fernet

    # 建立 Fernet 實例並快取
    key = _get_encryption_key()
    _cached_fernet = Fernet(key)

    return _cached_fernet

def encrypt_data(data: str) -> str:
    """
    加密資料（JSON 字串）
    返回 base64 編碼的加密資料
    """
    try:
        f = _get_fernet()  # 使用快取的 Fernet 實例
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        raise ValueError(f"加密失敗: {str(e)}")

def decrypt_data(encrypted_data: str) -> str:
    """
    解密資料
    返回原始 JSON 字串
    """
    try:
        f = _get_fernet()  # 使用快取的 Fernet 實例
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"解密失敗: 檔案可能已損壞或不是由此應用程式匯出")


# ===== 欄位加密功能 (用於資料庫敏感欄位) =====

def encrypt_field(text: Optional[str]) -> Optional[str]:
    """
    加密資料庫欄位文字

    Args:
        text: 要加密的文字，可為 None 或空字串

    Returns:
        加密後的文字，如果輸入為 None 或空字串則返回原值

    ⚡ 效能優化：使用快取的 Fernet 實例
    """
    if not text:
        return text

    try:
        f = _get_fernet()  # 使用快取的 Fernet 實例
        encrypted_bytes = f.encrypt(text.encode('utf-8'))
        # 直接返回 bytes 解碼後的字串（Fernet 輸出已經是 base64 格式）
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        # 如果加密失敗，記錄錯誤但返回原始文字（確保系統可用性）
        print(f"Field encryption error: {e}")
        return text


def decrypt_field(encrypted_text: Optional[str]) -> Optional[str]:
    """
    解密資料庫欄位文字

    Args:
        encrypted_text: 加密的文字，可為 None 或空字串

    Returns:
        解密後的文字，如果輸入為 None 或空字串則返回原值
        如果解密失敗（舊資料未加密），返回原始文字以保持向後相容

    ⚡ 效能優化：使用快取的 Fernet 實例
    """
    if not encrypted_text:
        return encrypted_text

    try:
        f = _get_fernet()  # 使用快取的 Fernet 實例
        decrypted_bytes = f.decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # 如果解密失敗，可能是未加密的舊資料
        # 返回原始文字以保持向後兼容
        return encrypted_text
