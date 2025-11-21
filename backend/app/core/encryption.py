from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from app.core.config import settings

def _get_encryption_key() -> bytes:
    """
    從 DATA_ENCRYPTION_KEY 生成 Fernet 密鑰
    使用 PBKDF2HMAC 將密鑰派生為標準格式
    """
    # 使用固定的 salt（因為我們需要一致的密鑰）
    salt = b'accounting_app_salt_v1'

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )

    key = base64.urlsafe_b64encode(kdf.derive(settings.DATA_ENCRYPTION_KEY.encode()))
    return key

def encrypt_data(data: str) -> str:
    """
    加密資料（JSON 字串）
    返回 base64 編碼的加密資料
    """
    try:
        key = _get_encryption_key()
        f = Fernet(key)
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
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"解密失敗: 檔案可能已損壞或不是由此應用程式匯出")
