from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime, timezone
import pytz
from app.core.database import get_db
from app.models.user import User
from app.models.budget import Budget
from app.models.budget_account import BudgetAccount
from app.models.budget_category import BudgetCategory
from app.models.transaction import Transaction
from app.schemas.budget import Budget as BudgetSchema, BudgetCreate, BudgetUpdate
from app.api.deps import get_current_user
from app.utils.budget_period import calculate_period_range, calculate_next_period_range

router = APIRouter()

# Taipei timezone
TAIPEI_TZ = pytz.timezone('Asia/Taipei')

def calculate_dynamic_daily_limit(budget: Budget, spent: float) -> float:
    """計算動態每日預算

    邏輯：
    1. 計算預算週期的總天數
    2. 計算今天距離週期結束還有多少天（剩餘天數）
    3. 計算剩餘預算 = 總預算 - 已花費
    4. 動態每日預算 = 剩餘預算 / 剩餘天數

    如果超支或已結束，返回 0
    """
    # 獲取當前時間（台北時區）
    now = datetime.now(TAIPEI_TZ)

    # 確保預算日期有時區資訊
    if budget.start_date.tzinfo is None:
        start_date = TAIPEI_TZ.localize(budget.start_date)
    else:
        start_date = budget.start_date.astimezone(TAIPEI_TZ)

    if budget.end_date.tzinfo is None:
        end_date = TAIPEI_TZ.localize(budget.end_date)
    else:
        end_date = budget.end_date.astimezone(TAIPEI_TZ)

    # 如果預算還沒開始，使用開始日期作為計算基準
    if now < start_date:
        days_passed = 0
        remaining_days = (end_date.date() - start_date.date()).days + 1
    # 如果預算已結束，返回 0
    elif now > end_date:
        return 0.0
    else:
        # 預算進行中
        days_passed = (now.date() - start_date.date()).days
        remaining_days = (end_date.date() - now.date()).days + 1  # 包含今天

    # 確保至少有 1 天避免除以 0
    if remaining_days < 1:
        remaining_days = 1

    # 計算剩餘預算
    remaining_budget = budget.amount - spent

    # 如果剩餘預算為負（超支），返回 0
    if remaining_budget <= 0:
        return 0.0

    # 動態每日預算 = 剩餘預算 / 剩餘天數
    dynamic_daily_limit = remaining_budget / remaining_days

    return round(dynamic_daily_limit, 2)

def calculate_budget_spent(db: Session, budget: Budget, category_names: List[str] = None) -> float:
    """計算預算已使用金額（只計算支出類型的交易）

    邏輯說明：
    - 如果預算沒有綁定帳戶：計算使用者所有帳戶的支出
    - 如果預算綁定了帳戶：只計算這些帳戶的支出
    - 如果預算沒有綁定類別（空列表）：計算所有類別的支出
    - 如果預算綁定了類別：只計算這些類別的交易
    - 排除 exclude_from_budget=True 的交易
    """
    # 獲取預算綁定的帳戶ID列表
    account_ids = [acc.id for acc in budget.accounts]

    # 建立基礎查詢 - 包含 debit 和 installment 類型
    query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type.in_(['debit', 'installment']),  # 計算支出和分期
        Transaction.transaction_date >= budget.start_date,
        Transaction.transaction_date <= budget.end_date,
        Transaction.exclude_from_budget == False  # 排除不計入預算的交易
    )

    # 如果有綁定帳戶，只計算這些帳戶的交易
    if account_ids:
        query = query.filter(Transaction.account_id.in_(account_ids))
    else:
        # 沒有綁定帳戶，計算該使用者所有帳戶的交易
        from app.models.account import Account
        user_account_ids = db.query(Account.id).filter(Account.user_id == budget.user_id).all()
        user_account_ids = [acc_id[0] for acc_id in user_account_ids]
        query = query.filter(Transaction.account_id.in_(user_account_ids))

    # 如果有指定類別列表且不為空，則只計算這些類別的交易
    if category_names and len(category_names) > 0:
        query = query.filter(Transaction.category.in_(category_names))

    spent = query.scalar()
    return spent or 0.0

@router.get("/", response_model=List[BudgetSchema])
def get_budgets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 使用 joinedload 預載入關聯的帳戶
    budgets = db.query(Budget).options(joinedload(Budget.accounts)).filter(Budget.user_id == current_user.id).all()

    # 自動更新每個預算的已使用金額，並設置 account_ids 和 category_names
    result = []
    for budget in budgets:
        # 獲取綁定的類別名稱列表
        category_names = list(set([bc.category_name for bc in db.query(BudgetCategory).filter(BudgetCategory.budget_id == budget.id).all()]))

        # 計算已使用金額（傳入類別名稱列表）
        budget.spent = calculate_budget_spent(db, budget, category_names)

        # 計算每日預算（根據模式）
        if budget.daily_limit_mode == 'auto':
            # 系統自動計算動態每日預算
            calculated_daily_limit = calculate_dynamic_daily_limit(budget, budget.spent)
        else:
            # 手動填寫模式，使用原有的 daily_limit
            calculated_daily_limit = budget.daily_limit

        # 將 Budget ORM 對象轉換為字典並添加 account_ids 和 category_names
        budget_dict = {
            "id": budget.id,
            "name": budget.name,
            "category_names": category_names,  # 使用多類別
            "amount": budget.amount,
            "daily_limit": calculated_daily_limit,
            "daily_limit_mode": budget.daily_limit_mode,
            "spent": budget.spent,
            "range_mode": budget.range_mode,
            "period": budget.period,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "account_ids": [acc.id for acc in budget.accounts],
            "user_id": budget.user_id,
            "parent_budget_id": budget.parent_budget_id,
            "is_latest_period": budget.is_latest_period,
            "created_at": budget.created_at,
            "updated_at": budget.updated_at
        }
        result.append(budget_dict)
    # db.commit()  # Do not commit changes on GET request

    return result

@router.post("/", response_model=BudgetSchema)
def create_budget(
    budget: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget_data = budget.dict()
    account_ids = budget_data.pop('account_ids', [])  # 提取 account_ids
    category_names = budget_data.pop('category_names', [])  # 提取 category_names

    # 如果是週期模式,自動計算開始和結束時間
    if budget_data['range_mode'] == 'recurring':
        if not budget_data.get('period'):
            raise HTTPException(status_code=400, detail="Period is required for recurring budgets")

        start_date, end_date = calculate_period_range(budget_data['period'])
        budget_data['start_date'] = start_date
        budget_data['end_date'] = end_date
    else:
        # 自訂區間模式,檢查必填欄位
        if not budget_data.get('start_date') or not budget_data.get('end_date'):
            raise HTTPException(status_code=400, detail="start_date and end_date are required for custom range budgets")

    # 創建預算（不包含 account_ids 和 category_names）
    db_budget = Budget(**budget_data, user_id=current_user.id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)

    # 建立預算與帳戶的關聯
    if account_ids:
        from app.models.account import Account
        # 驗證帳戶是否屬於當前使用者
        for account_id in account_ids:
            account = db.query(Account).filter(
                Account.id == account_id,
                Account.user_id == current_user.id
            ).first()
            if not account:
                db.delete(db_budget)
                db.commit()
                raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

            # 創建關聯記錄
            budget_account = BudgetAccount(budget_id=db_budget.id, account_id=account_id)
            db.add(budget_account)

    # 建立預算與類別的關聯
    if category_names:
        # 去除重複的類別名稱
        unique_category_names = list(set(category_names))
        for category_name in unique_category_names:
            budget_category = BudgetCategory(budget_id=db_budget.id, category_name=category_name)
            db.add(budget_category)

    db.commit()
    db.refresh(db_budget)

    # 計算每日預算（根據模式）
    if db_budget.daily_limit_mode == 'auto':
        calculated_daily_limit = calculate_dynamic_daily_limit(db_budget, db_budget.spent)
    else:
        calculated_daily_limit = db_budget.daily_limit

    # 返回包含 account_ids 和 category_names 的結果
    return {
        "id": db_budget.id,
        "name": db_budget.name,
        "category_names": unique_category_names,
        "amount": db_budget.amount,
        "daily_limit": calculated_daily_limit,
        "daily_limit_mode": db_budget.daily_limit_mode,
        "spent": db_budget.spent,
        "range_mode": db_budget.range_mode,
        "period": db_budget.period,
        "start_date": db_budget.start_date,
        "end_date": db_budget.end_date,
        "account_ids": [acc.id for acc in db_budget.accounts],
        "user_id": db_budget.user_id,
        "parent_budget_id": db_budget.parent_budget_id,
        "is_latest_period": db_budget.is_latest_period,
        "created_at": db_budget.created_at,
        "updated_at": db_budget.updated_at
    }

@router.get("/{budget_id}", response_model=BudgetSchema)
def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).options(joinedload(Budget.accounts)).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # 獲取綁定的類別名稱列表
    category_names = [bc.category_name for bc in db.query(BudgetCategory).filter(BudgetCategory.budget_id == budget.id).all()]
    # 去除重複顯示
    category_names = list(set(category_names))

    # 自動更新已使用金額
    budget.spent = calculate_budget_spent(db, budget, category_names)
    # db.commit()  # Do not commit changes on GET request

    # 計算每日預算（根據模式）
    if budget.daily_limit_mode == 'auto':
        calculated_daily_limit = calculate_dynamic_daily_limit(budget, budget.spent)
    else:
        calculated_daily_limit = budget.daily_limit

    return {
        "id": budget.id,
        "name": budget.name,
        "category_names": category_names,
        "amount": budget.amount,
        "daily_limit": calculated_daily_limit,
        "daily_limit_mode": budget.daily_limit_mode,
        "spent": budget.spent,
        "range_mode": budget.range_mode,
        "period": budget.period,
        "start_date": budget.start_date,
        "end_date": budget.end_date,
        "account_ids": [acc.id for acc in budget.accounts],
        "user_id": budget.user_id,
        "parent_budget_id": budget.parent_budget_id,
        "is_latest_period": budget.is_latest_period,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at
    }

@router.put("/{budget_id}", response_model=BudgetSchema)
def update_budget(
    budget_id: int,
    budget_update: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    update_data = budget_update.dict(exclude_unset=True)
    account_ids = update_data.pop('account_ids', None)  # 提取 account_ids
    category_names = update_data.pop('category_names', None)  # 提取 category_names

    # 更新預算基本資訊
    for key, value in update_data.items():
        setattr(budget, key, value)

    # 如果有更新 account_ids，則更新關聯
    if account_ids is not None:
        from app.models.account import Account
        # 刪除舊的關聯
        db.query(BudgetAccount).filter(BudgetAccount.budget_id == budget_id).delete()

        # 創建新的關聯
        if account_ids:
            for account_id in account_ids:
                account = db.query(Account).filter(
                    Account.id == account_id,
                    Account.user_id == current_user.id
                ).first()
                if not account:
                    raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

                budget_account = BudgetAccount(budget_id=budget_id, account_id=account_id)
                db.add(budget_account)

    # 如果有更新 category_names，則更新關聯
    if category_names is not None:
        # 刪除舊的關聯
        db.query(BudgetCategory).filter(BudgetCategory.budget_id == budget_id).delete()

        # 創建新的關聯
        if category_names:
            # 去除重複的類別名稱
            unique_category_names = list(set(category_names))
            for category_name in unique_category_names:
                budget_category = BudgetCategory(budget_id=budget_id, category_name=category_name)
                db.add(budget_category)

    db.commit()
    db.refresh(budget)

    # 獲取更新後的類別名稱列表
    updated_category_names = [bc.category_name for bc in db.query(BudgetCategory).filter(BudgetCategory.budget_id == budget_id).all()]

    # 計算每日預算（根據模式）
    if budget.daily_limit_mode == 'auto':
        calculated_daily_limit = calculate_dynamic_daily_limit(budget, budget.spent)
    else:
        calculated_daily_limit = budget.daily_limit

    return {
        "id": budget.id,
        "name": budget.name,
        "category_names": updated_category_names,
        "amount": budget.amount,
        "daily_limit": calculated_daily_limit,
        "daily_limit_mode": budget.daily_limit_mode,
        "spent": budget.spent,
        "range_mode": budget.range_mode,
        "period": budget.period,
        "start_date": budget.start_date,
        "end_date": budget.end_date,
        "account_ids": [acc.id for acc in budget.accounts],
        "user_id": budget.user_id,
        "parent_budget_id": budget.parent_budget_id,
        "is_latest_period": budget.is_latest_period,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at
    }

@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # 如果是週期模式且是最新週期,標記為取消(不再自動生成下一週期)
    if budget.range_mode == 'recurring' and budget.is_latest_period:
        # 找出所有同一週期鏈的預算,將它們的 is_latest_period 設為 False
        # 這樣就不會再自動生成新週期
        current_budget = budget
        while current_budget:
            current_budget.is_latest_period = False
            # 往前追溯到父預算
            if current_budget.parent_budget_id:
                current_budget = db.query(Budget).filter(Budget.id == current_budget.parent_budget_id).first()
            else:
                break
        db.commit()

    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}
