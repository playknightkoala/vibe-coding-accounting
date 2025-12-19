"""
Budget statistics calculator service
計算預算的每日統計資訊（超支天數、預算內天數）
"""

from datetime import datetime, timedelta, date
from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session
import pytz

from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.budget_category import BudgetCategory

# Taipei timezone
TAIPEI_TZ = pytz.timezone('Asia/Taipei')


def calculate_daily_spent(
    db: Session,
    budget: Budget,
    target_date: date,
    category_names: List[str] = None
) -> float:
    """計算指定日期的支出金額

    Args:
        db: Database session
        budget: Budget object
        target_date: 目標日期
        category_names: 類別名稱列表（可選）

    Returns:
        該日的總支出金額
    """
    # 獲取預算綁定的帳戶ID列表
    account_ids = [acc.id for acc in budget.accounts]

    # 設置日期範圍：從當天 00:00:00 到 23:59:59
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())

    # 轉換為 UTC（資料庫儲存為 UTC）
    start_datetime = TAIPEI_TZ.localize(start_datetime).astimezone(pytz.UTC)
    end_datetime = TAIPEI_TZ.localize(end_datetime).astimezone(pytz.UTC)

    # 建立基礎查詢 - 包含 debit 和 installment 類型
    query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type.in_(['debit', 'installment']),
        Transaction.transaction_date >= start_datetime,
        Transaction.transaction_date <= end_datetime,
        Transaction.exclude_from_budget == False
    )

    # 如果有綁定帳戶，只計算這些帳戶的交易
    if account_ids:
        query = query.filter(Transaction.account_id.in_(account_ids))
    else:
        # 沒有綁定帳戶，計算該使用者所有帳戶的交易
        user_account_ids = db.query(Account.id).filter(
            Account.user_id == budget.user_id
        ).all()
        user_account_ids = [acc_id[0] for acc_id in user_account_ids]
        query = query.filter(Transaction.account_id.in_(user_account_ids))

    # 如果有指定類別列表且不為空，則只計算這些類別的交易
    if category_names and len(category_names) > 0:
        query = query.filter(Transaction.category.in_(category_names))

    spent = query.scalar()
    return spent or 0.0


def calculate_budget_stats(db: Session, budget: Budget) -> tuple:
    """計算預算的統計資訊

    Args:
        db: Database session
        budget: Budget object

    Returns:
        (over_budget_days, within_budget_days) tuple
    """
    # 獲取綁定的類別名稱列表
    category_names = list(set([
        bc.category_name
        for bc in db.query(BudgetCategory).filter(
            BudgetCategory.budget_id == budget.id
        ).all()
    ]))

    # 計算日期範圍
    today = datetime.now(TAIPEI_TZ).date()
    start_date = budget.start_date.astimezone(TAIPEI_TZ).date()
    end_date = budget.end_date.astimezone(TAIPEI_TZ).date()

    # 只統計已經過去的日期（不包含今天及未來）
    last_date = min(today - timedelta(days=1), end_date)

    # 如果預算還未開始，或已結束很久，返回 (0, 0)
    if start_date > last_date:
        return (0, 0)

    # 計算總天數（用於 auto 模式的平均計算）
    total_days = (end_date - start_date).days + 1

    # 計算每日預算限額
    if budget.daily_limit_mode == 'manual':
        # Manual 模式：使用用戶設定的 daily_limit
        daily_limit = budget.daily_limit or 0
    else:
        # Auto 模式：使用平均值（總預算 / 總天數）
        daily_limit = budget.amount / total_days if total_days > 0 else 0

    # 初始化計數器
    over_budget_days = 0
    within_budget_days = 0

    # 遍歷每一天進行統計
    current_date = start_date
    while current_date <= last_date:
        # 計算該天的支出
        daily_spent = calculate_daily_spent(
            db,
            budget,
            current_date,
            category_names
        )

        # 判斷是否超支
        if daily_spent > daily_limit:
            over_budget_days += 1
        else:
            within_budget_days += 1

        # 移動到下一天
        current_date += timedelta(days=1)

    return (over_budget_days, within_budget_days)


def update_budget_stats(db: Session, budget: Budget) -> Budget:
    """更新預算的統計資訊並保存到資料庫

    Args:
        db: Database session
        budget: Budget object

    Returns:
        Updated Budget object
    """
    over_budget_days, within_budget_days = calculate_budget_stats(db, budget)

    budget.over_budget_days = over_budget_days
    budget.within_budget_days = within_budget_days
    budget.last_stats_update = datetime.now(pytz.UTC)

    db.commit()
    db.refresh(budget)

    return budget


def update_all_active_budgets_stats(db: Session) -> int:
    """更新所有活躍預算的統計資訊

    用於定時任務，每日更新所有預算的統計

    Args:
        db: Database session

    Returns:
        更新的預算數量
    """
    from sqlalchemy.orm import joinedload

    today = datetime.now(TAIPEI_TZ).date()
    today_datetime = TAIPEI_TZ.localize(
        datetime.combine(today, datetime.min.time())
    ).astimezone(pytz.UTC)

    # 查詢所有活躍的預算（結束日期 >= 今天）
    active_budgets = db.query(Budget).options(
        joinedload(Budget.accounts)
    ).filter(
        Budget.end_date >= today_datetime
    ).all()

    updated_count = 0
    for budget in active_budgets:
        try:
            update_budget_stats(db, budget)
            updated_count += 1
        except Exception as e:
            print(f"Failed to update stats for budget {budget.id}: {str(e)}")
            continue

    return updated_count
