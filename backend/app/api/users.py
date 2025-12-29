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
from app.services.budget_stats import update_budget_stats
from app.models.budget_category import BudgetCategory
from app.models.budget_account import BudgetAccount
from app.models.category import Category
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

        # 查詢所有類別
        categories = db.query(Category).filter(Category.user_id == current_user.id).order_by(Category.order_index).all()

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
                    "note": trans.note,
                    "foreign_amount": float(trans.foreign_amount) if trans.foreign_amount else None,
                    "foreign_currency": trans.foreign_currency,
                    "transaction_date": trans.transaction_date.isoformat() if trans.transaction_date else None,
                    "is_installment": trans.is_installment,
                    "installment_group_id": trans.installment_group_id,
                    "installment_number": trans.installment_number,
                    "total_installments": trans.total_installments,
                    "total_amount": float(trans.total_amount) if trans.total_amount else None,
                    "remaining_amount": float(trans.remaining_amount) if trans.remaining_amount else None,
                    "exclude_from_budget": trans.exclude_from_budget,
                    "created_at": trans.created_at.isoformat() if trans.created_at else None
                }
                for trans in transactions
            ],
            "categories": [
                {
                    "name": cat.name,
                    "order_index": cat.order_index,
                    "created_at": cat.created_at.isoformat() if cat.created_at else None
                }
                for cat in categories
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
                "daily_limit_mode": budget.daily_limit_mode,
                "spent": float(budget.spent),
                "range_mode": budget.range_mode,
                "period": budget.period,
                "start_date": budget.start_date.isoformat() if budget.start_date else None,
                "end_date": budget.end_date.isoformat() if budget.end_date else None,

                "account_indices": account_indices,
                "is_primary": budget.is_primary,
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
            "categories_created": 0,
            "categories_updated": 0,
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
                # 覆蓋現有帳戶（直接使用匯出時保存的餘額）
                existing_account.balance = acc_data["balance"]
                existing_account.description = acc_data.get("description")

                # 刪除該帳戶的所有舊交易
                db.query(Transaction).filter(Transaction.account_id == existing_account.id).delete()

                account_index_to_new_id[acc_data["index"]] = existing_account.id
                stats["accounts_updated"] += 1
            else:
                # 新增帳戶（直接使用匯出時保存的餘額）
                new_account = Account(
                    user_id=current_user.id,
                    name=acc_data["name"],
                    account_type=acc_data["account_type"],
                    balance=acc_data["balance"],
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
                # 更新現有交易（不調整餘額，因為帳戶餘額已直接使用匯出值）

                # 更新交易資料
                existing_transaction.amount = trans_data["amount"]
                existing_transaction.transaction_type = trans_data["transaction_type"]
                existing_transaction.category = trans_data.get("category")
                existing_transaction.note = trans_data.get("note")
                existing_transaction.foreign_amount = trans_data.get("foreign_amount")
                existing_transaction.foreign_currency = trans_data.get("foreign_currency")
                existing_transaction.is_installment = trans_data.get("is_installment", False)
                existing_transaction.installment_group_id = trans_data.get("installment_group_id")
                existing_transaction.installment_number = trans_data.get("installment_number")
                existing_transaction.total_installments = trans_data.get("total_installments")
                existing_transaction.total_amount = trans_data.get("total_amount")
                existing_transaction.remaining_amount = trans_data.get("remaining_amount")
                existing_transaction.exclude_from_budget = trans_data.get("exclude_from_budget", False)

                # 不調整餘額（帳戶餘額已直接使用匯出時保存的值）

                stats["transactions_updated"] += 1
            else:
                # 新增交易
                new_transaction = Transaction(
                    account_id=account_id,
                    description=trans_data["description"],
                    amount=trans_data["amount"],
                    transaction_type=trans_data["transaction_type"],
                    category=trans_data.get("category"),
                    note=trans_data.get("note"),
                    foreign_amount=trans_data.get("foreign_amount"),
                    foreign_currency=trans_data.get("foreign_currency"),
                    transaction_date=trans_date,
                    is_installment=trans_data.get("is_installment", False),
                    installment_group_id=trans_data.get("installment_group_id"),
                    installment_number=trans_data.get("installment_number"),
                    total_installments=trans_data.get("total_installments"),
                    total_amount=trans_data.get("total_amount"),
                    remaining_amount=trans_data.get("remaining_amount"),
                    exclude_from_budget=trans_data.get("exclude_from_budget", False)
                )
                db.add(new_transaction)

                # 不調整餘額（帳戶餘額已直接使用匯出時保存的值）

                stats["transactions_created"] += 1

        # 匯入類別（覆蓋或新增）
        for cat_data in import_data.get("categories", []):
            # 查找是否已存在相同名稱的類別
            existing_category = db.query(Category).filter(
                Category.user_id == current_user.id,
                Category.name == cat_data["name"]
            ).first()

            if existing_category:
                # 覆蓋現有類別
                existing_category.order_index = cat_data.get("order_index", 0)
                stats["categories_updated"] += 1
            else:
                # 新增類別
                new_category = Category(
                    user_id=current_user.id,
                    name=cat_data["name"],
                    order_index=cat_data.get("order_index", 0)
                )
                db.add(new_category)
                stats["categories_created"] += 1

        # 匯入預算（覆蓋或新增）
        imported_budgets = []  # 追蹤匯入的預算，用於後續統計計算

        for budget_data in import_data.get("budgets", []):
            # 轉換帳戶索引為帳戶 ID
            new_account_ids = [
                account_index_to_new_id[idx]
                for idx in budget_data.get("account_indices", [])
                if idx in account_index_to_new_id
            ]

            # 查找是否已存在相同名稱和時間範圍的預算（避免週期預算被誤判為重複）
            budget_start = datetime.fromisoformat(budget_data["start_date"]) if budget_data.get("start_date") else None
            budget_end = datetime.fromisoformat(budget_data["end_date"]) if budget_data.get("end_date") else None

            existing_budget = db.query(Budget).filter(
                Budget.user_id == current_user.id,
                Budget.name == budget_data["name"],
                Budget.start_date == budget_start,
                Budget.end_date == budget_end
            ).first()

            if existing_budget:
                # 覆蓋現有預算
                existing_budget.amount = budget_data["amount"]
                existing_budget.daily_limit = budget_data.get("daily_limit")
                existing_budget.daily_limit_mode = budget_data.get("daily_limit_mode", "manual")
                existing_budget.spent = budget_data.get("spent", 0)
                existing_budget.range_mode = budget_data["range_mode"]
                existing_budget.period = budget_data.get("period")

                existing_budget.start_date = datetime.fromisoformat(budget_data["start_date"]) if budget_data.get("start_date") else None
                existing_budget.end_date = datetime.fromisoformat(budget_data["end_date"]) if budget_data.get("end_date") else None
                existing_budget.is_primary = budget_data.get("is_primary", False)

                # 刪除舊的關聯
                db.query(BudgetCategory).filter(BudgetCategory.budget_id == existing_budget.id).delete()
                db.query(BudgetAccount).filter(BudgetAccount.budget_id == existing_budget.id).delete()

                # 新增預算類別關聯
                unique_category_names = list(set(budget_data.get("category_names", []) or []))
                for category_name in unique_category_names:
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
                imported_budgets.append(existing_budget)
            else:
                # 新增預算
                new_budget = Budget(
                    user_id=current_user.id,
                    name=budget_data["name"],
                    amount=budget_data["amount"],
                    daily_limit=budget_data.get("daily_limit"),
                    daily_limit_mode=budget_data.get("daily_limit_mode", "manual"),
                    spent=budget_data.get("spent", 0),
                    range_mode=budget_data["range_mode"],
                    period=budget_data.get("period"),

                    start_date=datetime.fromisoformat(budget_data["start_date"]) if budget_data.get("start_date") else None,
                    end_date=datetime.fromisoformat(budget_data["end_date"]) if budget_data.get("end_date") else None,
                    is_primary=budget_data.get("is_primary", False)
                )
                db.add(new_budget)
                db.flush()

                # 新增預算類別關聯
                unique_category_names = list(set(budget_data.get("category_names", []) or []))
                for category_name in unique_category_names:
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
                imported_budgets.append(new_budget)

        # 確保所有預算及其關聯資料都寫入資料庫
        db.flush()

        # 匯入完成後，計算匯入預算的統計資料
        for budget in imported_budgets:
            try:
                update_budget_stats(db, budget)
            except Exception as e:
                # 統計計算失敗不影響匯入，只記錄錯誤
                print(f"Failed to update stats for budget {budget.id}: {str(e)}")

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
        import traceback
        traceback.print_exc()
        print(f"Import Error Detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匯入資料失敗: {str(e)}"
        )

@router.delete("/me/clear-data")
def clear_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清除使用者所有資料（保留帳號）"""
    try:
        # 1. 先取得所有帳戶 ID
        account_ids = [acc.id for acc in db.query(Account).filter(Account.user_id == current_user.id).all()]

        # 2. 刪除所有交易（必須先刪除，因為有外鍵約束）
        if account_ids:
            db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).delete(synchronize_session=False)

        # 3. 刪除所有預算關聯
        budget_ids = [b.id for b in db.query(Budget).filter(Budget.user_id == current_user.id).all()]
        if budget_ids:
            db.query(BudgetCategory).filter(BudgetCategory.budget_id.in_(budget_ids)).delete(synchronize_session=False)
            db.query(BudgetAccount).filter(BudgetAccount.budget_id.in_(budget_ids)).delete(synchronize_session=False)

        # 4. 刪除所有預算
        db.query(Budget).filter(Budget.user_id == current_user.id).delete(synchronize_session=False)

        # 5. 刪除所有帳戶
        db.query(Account).filter(Account.user_id == current_user.id).delete(synchronize_session=False)

        # 6. 刪除所有類別
        db.query(Category).filter(Category.user_id == current_user.id).delete(synchronize_session=False)

        # 7. 創建預設帳戶（恢復到初始狀態）
        default_accounts = [
            Account(
                name="現金",
                account_type="cash",
                currency="TWD",
                description="預設現金帳戶",
                balance=0.0,
                user_id=current_user.id
            ),
            Account(
                name="預設銀行",
                account_type="bank",
                currency="TWD",
                description="預設銀行帳戶",
                balance=0.0,
                user_id=current_user.id
            )
        ]
        db.add_all(default_accounts)

        db.commit()

        return {
            "message": "所有資料已清除，帳號已恢復到初始狀態"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除資料失敗: {str(e)}"
        )

@router.delete("/me")
def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除使用者帳號及所有相關資料"""
    try:
        # 1. 先取得所有帳戶 ID
        account_ids = [acc.id for acc in db.query(Account).filter(Account.user_id == current_user.id).all()]

        # 2. 刪除所有交易（必須先刪除，因為有外鍵約束）
        if account_ids:
            db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).delete(synchronize_session=False)

        # 3. 刪除所有預算關聯
        budget_ids = [b.id for b in db.query(Budget).filter(Budget.user_id == current_user.id).all()]
        if budget_ids:
            db.query(BudgetCategory).filter(BudgetCategory.budget_id.in_(budget_ids)).delete(synchronize_session=False)
            db.query(BudgetAccount).filter(BudgetAccount.budget_id.in_(budget_ids)).delete(synchronize_session=False)

        # 4. 刪除所有預算
        db.query(Budget).filter(Budget.user_id == current_user.id).delete(synchronize_session=False)

        # 5. 刪除所有帳戶
        db.query(Account).filter(Account.user_id == current_user.id).delete(synchronize_session=False)

        # 6. 刪除所有類別
        db.query(Category).filter(Category.user_id == current_user.id).delete(synchronize_session=False)

        # 7. 刪除使用者帳號
        db.delete(current_user)

        db.commit()

        return {
            "message": "帳號已成功刪除"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除帳號失敗: {str(e)}"
        )
