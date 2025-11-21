from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.core.encryption import encrypt_data, decrypt_data
from app.api.deps import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.budget_category import BudgetCategory
from app.models.budget_account import BudgetAccount
from app.schemas.user import User as UserSchema, UserUpdate, TwoFactorSetup, TwoFactorVerify
import pyotp
import qrcode
import io
import base64
import json
from datetime import datetime
from typing import Dict, Any, List

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """取得目前使用者資訊"""
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新使用者資訊（密碼）"""
    if user_update.new_password:
        if not user_update.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必須提供目前密碼才能變更密碼"
            )

        # 驗證目前密碼
        if not verify_password(user_update.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目前密碼不正確"
            )

        # 更新密碼
        current_user.hashed_password = get_password_hash(user_update.new_password)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/2fa/setup", response_model=TwoFactorSetup)
def setup_two_factor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """設定 2FA（生成 QR code）"""
    # 生成新的 secret
    secret = pyotp.random_base32()

    # 暫時儲存 secret（等待驗證）
    current_user.two_factor_secret = secret
    db.commit()

    # 生成 TOTP URI
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.username,
        issuer_name="Accounting App"
    )

    # 生成 QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return TwoFactorSetup(
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_code_base64}"
    )

@router.post("/me/2fa/verify")
def verify_two_factor(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """驗證並啟用 2FA"""
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請先設定 2FA"
        )

    # 驗證 TOTP token
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(verification.token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驗證碼錯誤"
        )

    # 啟用 2FA
    current_user.two_factor_enabled = True
    db.commit()

    return {"message": "2FA 已成功啟用"}

@router.post("/me/2fa/disable")
def disable_two_factor(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停用 2FA"""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 尚未啟用"
        )

    # 驗證 TOTP token
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(verification.token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驗證碼錯誤"
        )

    # 停用 2FA
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    db.commit()

    return {"message": "2FA 已停用"}

@router.get("/me/export")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """匯出使用者所有資料（帳戶、交易、預算）"""
    try:
        # 查詢所有帳戶
        accounts = db.query(Account).filter(Account.user_id == current_user.id).all()

        # 查詢所有交易（通過帳戶關聯）
        account_ids = [acc.id for acc in accounts]
        transactions = db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).all() if account_ids else []

        # 查詢所有預算
        budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()

        # 建立帳戶 ID 映射（舊 ID -> 新索引）
        account_id_map = {acc.id: idx for idx, acc in enumerate(accounts)}

        # 準備匯出資料
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "user": {
                "username": current_user.username
            },
            "accounts": [
                {
                    "index": account_id_map[acc.id],
                    "name": acc.name,
                    "account_type": acc.account_type,
                    "balance": float(acc.balance),
                    "currency": acc.currency,
                    "description": acc.description,
                    "created_at": acc.created_at.isoformat() if acc.created_at else None
                }
                for acc in accounts
            ],
            "transactions": [
                {
                    "account_index": account_id_map[trans.account_id],
                    "description": trans.description,
                    "amount": float(trans.amount),
                    "transaction_type": trans.transaction_type,
                    "category": trans.category,
                    "transaction_date": trans.transaction_date.isoformat() if trans.transaction_date else None,
                    "created_at": trans.created_at.isoformat() if trans.created_at else None
                }
                for trans in transactions
            ],
            "budgets": []
        }

        # 處理預算資料
        for budget in budgets:
            # 查詢預算關聯的類別
            budget_categories = db.query(BudgetCategory).filter(BudgetCategory.budget_id == budget.id).all()
            category_names = [bc.category_name for bc in budget_categories]

            # 查詢預算關聯的帳戶
            budget_accounts = db.query(BudgetAccount).filter(BudgetAccount.budget_id == budget.id).all()
            account_indices = [account_id_map[ba.account_id] for ba in budget_accounts if ba.account_id in account_id_map]

            export_data["budgets"].append({
                "name": budget.name,
                "category_names": category_names,
                "amount": float(budget.amount),
                "daily_limit": float(budget.daily_limit) if budget.daily_limit else None,
                "spent": float(budget.spent),
                "range_mode": budget.range_mode,
                "period": budget.period,
                "start_date": budget.start_date.isoformat() if budget.start_date else None,
                "end_date": budget.end_date.isoformat() if budget.end_date else None,
                "account_indices": account_indices,
                "created_at": budget.created_at.isoformat() if budget.created_at else None
            })

        # 將資料轉換為 JSON 字串
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)

        # 加密資料
        encrypted_data = encrypt_data(json_str)

        # 建立加密封裝格式
        encrypted_export = {
            "app": "accounting_app",
            "encrypted": True,
            "version": "1.0",
            "data": encrypted_data
        }

        # 返回加密的 JSON 檔案
        filename = f"accounting_data_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        return JSONResponse(
            content=encrypted_export,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匯出資料失敗: {str(e)}"
        )

@router.post("/me/import")
async def import_user_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """匯入使用者資料（帳戶、交易、預算）"""
    try:
        # 讀取上傳的 JSON 檔案
        content = await file.read()
        file_data = json.loads(content)

        # 檢查是否為加密檔案
        if isinstance(file_data, dict) and file_data.get("encrypted") is True:
            # 驗證是否為此應用程式匯出的檔案
            if file_data.get("app") != "accounting_app":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="此檔案不是由本應用程式匯出"
                )

            # 解密資料
            try:
                encrypted_data = file_data.get("data")
                if not encrypted_data:
                    raise ValueError("找不到加密資料")

                decrypted_json = decrypt_data(encrypted_data)
                import_data = json.loads(decrypted_json)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        else:
            # 未加密的舊格式檔案（向後相容）
            import_data = file_data

        # 驗證資料格式
        if "version" not in import_data or "accounts" not in import_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的匯入檔案格式"
            )

        # 建立帳戶 ID 映射（舊索引 -> 新/現有 ID）
        account_index_to_new_id = {}

        stats = {
            "accounts_created": 0,
            "accounts_updated": 0,
            "transactions_created": 0,
            "transactions_updated": 0,
            "budgets_created": 0,
            "budgets_updated": 0
        }

        # 匯入帳戶（覆蓋或新增）
        for acc_data in import_data.get("accounts", []):
            # 查找是否已存在相同的帳戶（名稱、類型、幣別都相同）
            existing_account = db.query(Account).filter(
                Account.user_id == current_user.id,
                Account.name == acc_data["name"],
                Account.account_type == acc_data["account_type"],
                Account.currency == acc_data.get("currency", "TWD")
            ).first()

            if existing_account:
                # 覆蓋現有帳戶（先將餘額歸零，之後會透過交易重新計算）
                existing_account.balance = 0
                existing_account.description = acc_data.get("description")

                # 刪除該帳戶的所有舊交易
                db.query(Transaction).filter(Transaction.account_id == existing_account.id).delete()

                account_index_to_new_id[acc_data["index"]] = existing_account.id
                stats["accounts_updated"] += 1
            else:
                # 新增帳戶
                new_account = Account(
                    user_id=current_user.id,
                    name=acc_data["name"],
                    account_type=acc_data["account_type"],
                    balance=0,
                    currency=acc_data.get("currency", "TWD"),
                    description=acc_data.get("description")
                )
                db.add(new_account)
                db.flush()
                account_index_to_new_id[acc_data["index"]] = new_account.id
                stats["accounts_created"] += 1

        # 匯入交易（覆蓋或新增）
        for trans_data in import_data.get("transactions", []):
            account_index = trans_data["account_index"]
            if account_index not in account_index_to_new_id:
                continue  # 跳過無效的交易

            account_id = account_index_to_new_id[account_index]
            account = db.query(Account).filter(Account.id == account_id).first()

            trans_date = datetime.fromisoformat(trans_data["transaction_date"]) if trans_data.get("transaction_date") else datetime.now()

            # 查找是否已存在相同的交易（日期和描述都相同）
            existing_transaction = db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.transaction_date == trans_date,
                Transaction.description == trans_data["description"]
            ).first()

            if existing_transaction:
                # 先反轉舊交易對餘額的影響
                if existing_transaction.transaction_type == "credit":
                    account.balance -= existing_transaction.amount
                else:
                    account.balance += existing_transaction.amount

                # 更新交易資料
                existing_transaction.amount = trans_data["amount"]
                existing_transaction.transaction_type = trans_data["transaction_type"]
                existing_transaction.category = trans_data.get("category")

                # 應用新交易對餘額的影響
                if trans_data["transaction_type"] == "credit":
                    account.balance += trans_data["amount"]
                else:
                    account.balance -= trans_data["amount"]

                stats["transactions_updated"] += 1
            else:
                # 新增交易
                new_transaction = Transaction(
                    account_id=account_id,
                    description=trans_data["description"],
                    amount=trans_data["amount"],
                    transaction_type=trans_data["transaction_type"],
                    category=trans_data.get("category"),
                    transaction_date=trans_date
                )
                db.add(new_transaction)

                # 更新帳戶餘額
                if trans_data["transaction_type"] == "credit":
                    account.balance += trans_data["amount"]
                else:
                    account.balance -= trans_data["amount"]

                stats["transactions_created"] += 1

        # 匯入預算（覆蓋或新增）
        for budget_data in import_data.get("budgets", []):
            # 轉換帳戶索引為帳戶 ID
            new_account_ids = [
                account_index_to_new_id[idx]
                for idx in budget_data.get("account_indices", [])
                if idx in account_index_to_new_id
            ]

            # 查找是否已存在相同名稱的預算
            existing_budget = db.query(Budget).filter(
                Budget.user_id == current_user.id,
                Budget.name == budget_data["name"]
            ).first()

            if existing_budget:
                # 覆蓋現有預算
                existing_budget.amount = budget_data["amount"]
                existing_budget.daily_limit = budget_data.get("daily_limit")
                existing_budget.spent = budget_data.get("spent", 0)
                existing_budget.range_mode = budget_data["range_mode"]
                existing_budget.period = budget_data.get("period")
                existing_budget.start_date = datetime.fromisoformat(budget_data["start_date"]) if budget_data.get("start_date") else None
                existing_budget.end_date = datetime.fromisoformat(budget_data["end_date"]) if budget_data.get("end_date") else None

                # 刪除舊的關聯
                db.query(BudgetCategory).filter(BudgetCategory.budget_id == existing_budget.id).delete()
                db.query(BudgetAccount).filter(BudgetAccount.budget_id == existing_budget.id).delete()

                # 新增預算類別關聯
                for category_name in budget_data.get("category_names", []):
                    budget_category = BudgetCategory(
                        budget_id=existing_budget.id,
                        category_name=category_name
                    )
                    db.add(budget_category)

                # 新增預算帳戶關聯
                for account_id in new_account_ids:
                    budget_account = BudgetAccount(
                        budget_id=existing_budget.id,
                        account_id=account_id
                    )
                    db.add(budget_account)

                stats["budgets_updated"] += 1
            else:
                # 新增預算
                new_budget = Budget(
                    user_id=current_user.id,
                    name=budget_data["name"],
                    amount=budget_data["amount"],
                    daily_limit=budget_data.get("daily_limit"),
                    spent=budget_data.get("spent", 0),
                    range_mode=budget_data["range_mode"],
                    period=budget_data.get("period"),
                    start_date=datetime.fromisoformat(budget_data["start_date"]) if budget_data.get("start_date") else None,
                    end_date=datetime.fromisoformat(budget_data["end_date"]) if budget_data.get("end_date") else None
                )
                db.add(new_budget)
                db.flush()

                # 新增預算類別關聯
                for category_name in budget_data.get("category_names", []):
                    budget_category = BudgetCategory(
                        budget_id=new_budget.id,
                        category_name=category_name
                    )
                    db.add(budget_category)

                # 新增預算帳戶關聯
                for account_id in new_account_ids:
                    budget_account = BudgetAccount(
                        budget_id=new_budget.id,
                        account_id=account_id
                    )
                    db.add(budget_account)

                stats["budgets_created"] += 1

        db.commit()

        return {
            "message": "資料匯入成功",
            "stats": stats
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無效的 JSON 檔案格式"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匯入資料失敗: {str(e)}"
        )
