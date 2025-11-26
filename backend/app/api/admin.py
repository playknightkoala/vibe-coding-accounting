from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.account import Account
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.user import UserAdminInfo, AdminUserUpdate
from app.api.deps import get_current_admin

router = APIRouter()

@router.get("/users", response_model=List[UserAdminInfo])
def list_all_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """列出所有使用者及其統計資訊"""
    users = db.query(User).all()

    result = []
    for user in users:
        # 計算統計資訊
        transaction_count = db.query(func.count(Transaction.id)).join(Account).filter(
            Account.user_id == user.id
        ).scalar() or 0

        budget_count = db.query(func.count(Budget.id)).filter(
            Budget.user_id == user.id
        ).scalar() or 0

        account_count = db.query(func.count(Account.id)).filter(
            Account.user_id == user.id
        ).scalar() or 0

        user_info = UserAdminInfo(
            id=user.id,
            email=user.username,
            is_google_user=user.is_google_user,
            is_admin=user.is_admin,
            is_blocked=user.is_blocked,
            two_factor_enabled=user.two_factor_enabled,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            transaction_count=transaction_count,
            budget_count=budget_count,
            account_count=account_count
        )
        result.append(user_info)

    return result

@router.get("/users/{user_id}", response_model=UserAdminInfo)
def get_user_info(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """獲取特定使用者的詳細資訊"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    # 計算統計資訊
    transaction_count = db.query(func.count(Transaction.id)).join(Account).filter(
        Account.user_id == user.id
    ).scalar() or 0

    budget_count = db.query(func.count(Budget.id)).filter(
        Budget.user_id == user.id
    ).scalar() or 0

    account_count = db.query(func.count(Account.id)).filter(
        Account.user_id == user.id
    ).scalar() or 0

    return UserAdminInfo(
        id=user.id,
        email=user.username,
        is_google_user=user.is_google_user,
        is_admin=user.is_admin,
        is_blocked=user.is_blocked,
        two_factor_enabled=user.two_factor_enabled,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        transaction_count=transaction_count,
        budget_count=budget_count,
        account_count=account_count
    )

@router.patch("/users/{user_id}", response_model=UserAdminInfo)
def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新使用者資訊 (管理員專用)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    # 防止管理員移除自己的管理員權限
    if user.id == current_admin.id and user_update.is_admin is False:
        raise HTTPException(status_code=400, detail="不能移除自己的管理員權限")

    # 更新欄位
    update_data = user_update.dict(exclude_unset=True)

    # 處理密碼更新
    if 'password' in update_data and update_data['password']:
        if user.is_google_user:
            raise HTTPException(status_code=400, detail="Google 登入的使用者無法設定密碼")
        update_data['hashed_password'] = get_password_hash(update_data.pop('password'))

    # 處理 email 更新
    if 'email' in update_data and update_data['email']:
        # 檢查新 email 是否已被使用
        existing_user = db.query(User).filter(
            User.username == update_data['email'],
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="此電子郵件已被使用")

        if user.is_google_user:
            raise HTTPException(status_code=400, detail="Google 登入的使用者無法更改電子郵件")

        user.username = update_data.pop('email')

    # 處理 2FA 取消
    if 'two_factor_enabled' in update_data and not update_data['two_factor_enabled']:
        user.two_factor_secret = None

    # 更新其他欄位
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)

    # 返回更新後的資訊
    return get_user_info(user_id, current_admin, db)

@router.post("/users/{user_id}/reset-data")
def reset_user_data(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """清除使用者所有資料,恢復到剛建立帳號的狀態"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    # 防止管理員重置自己的帳號
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能重置自己的帳號")

    # 刪除所有交易記錄 (透過 cascade 自動刪除)
    # 刪除所有預算
    db.query(Budget).filter(Budget.user_id == user_id).delete()

    # 刪除所有帳戶 (會自動刪除相關交易)
    db.query(Account).filter(Account.user_id == user_id).delete()

    # 重置 2FA
    user.two_factor_enabled = False
    user.two_factor_secret = None

    # 建立預設帳戶
    default_accounts = [
        Account(
            name="現金",
            account_type="cash",
            currency="TWD",
            description="預設現金帳戶",
            balance=0.0,
            user_id=user.id
        ),
        Account(
            name="預設銀行",
            account_type="bank",
            currency="TWD",
            description="預設銀行帳戶",
            balance=0.0,
            user_id=user.id
        )
    ]

    for account in default_accounts:
        db.add(account)

    db.commit()

    return {"message": f"使用者 {user.username} 的資料已重置"}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """完全刪除使用者及其所有資料"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    # 防止管理員刪除自己
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能刪除自己的帳號")

    email = user.username

    # 刪除使用者 (cascade 會自動刪除所有相關資料)
    db.delete(user)
    db.commit()

    return {"message": f"使用者 {email} 已完全刪除"}

@router.post("/users/{user_id}/block")
def block_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """封鎖使用者"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    # 防止管理員封鎖自己
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能封鎖自己")

    user.is_blocked = True
    db.commit()

    return {"message": f"使用者 {user.username} 已被封鎖"}

@router.post("/users/{user_id}/unblock")
def unblock_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """解除封鎖使用者"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    user.is_blocked = False
    db.commit()

    return {"message": f"使用者 {user.username} 已解除封鎖"}
