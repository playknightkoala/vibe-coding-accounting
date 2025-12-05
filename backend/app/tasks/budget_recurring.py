"""
預算週期自動生成任務
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.budget import Budget
from app.models.budget_account import BudgetAccount
from app.models.budget_category import BudgetCategory
from app.utils.budget_period import calculate_next_period_range
import logging

logger = logging.getLogger(__name__)


def create_next_period_budgets():
    """
    檢查所有週期預算,如果結束時間已到,自動建立下一個週期
    此函數應該由排程任務(cron job)定期執行
    """
    db: Session = SessionLocal()
    try:
        now = datetime.now()

        # 查找所有需要自動續期的預算:
        # 1. range_mode = 'recurring'
        # 2. is_latest_period = True (表示使用者沒有取消)
        # 3. end_date <= now (週期已結束)
        budgets_to_renew = db.query(Budget).filter(
            Budget.range_mode == 'recurring',
            Budget.is_latest_period == True,
            Budget.end_date <= now
        ).all()

        created_count = 0

        for budget in budgets_to_renew:
            # 計算下一個週期的時間範圍
            next_start, next_end = calculate_next_period_range(budget.period, budget.end_date)

            # 檢查是否已經存在下一個週期的預算（防止重複生成）
            # 方法1: 查找所有以當前預算為 parent 的子預算
            child_budgets = db.query(Budget).filter(
                Budget.parent_budget_id == budget.id
            ).all()

            # 檢查是否已有符合下一週期時間的子預算
            existing_next_period = False
            existing_budget_id = None
            for child in child_budgets:
                if child.start_date == next_start and child.end_date == next_end:
                    existing_next_period = True
                    existing_budget_id = child.id
                    logger.info(f"Budget '{budget.name}' for period {next_start} to {next_end} already exists (ID: {child.id}, method: parent_check), skipping")
                    break

            # 方法2: 如果透過 parent 找不到，檢查是否有相同名稱、時間範圍和使用者的預算（處理匯入資料的情況）
            if not existing_next_period:
                same_period_budget = db.query(Budget).filter(
                    Budget.user_id == budget.user_id,
                    Budget.name == budget.name,
                    Budget.range_mode == 'recurring',
                    Budget.period == budget.period,
                    Budget.start_date == next_start,
                    Budget.end_date == next_end
                ).first()

                if same_period_budget:
                    existing_next_period = True
                    existing_budget_id = same_period_budget.id
                    logger.info(f"Budget '{budget.name}' for period {next_start} to {next_end} already exists (ID: {same_period_budget.id}, method: period_check), skipping")

                    # 如果找到的預算沒有正確的 parent_budget_id，修正它
                    if same_period_budget.parent_budget_id != budget.id:
                        same_period_budget.parent_budget_id = budget.id
                        logger.info(f"Fixed parent_budget_id for budget ID {same_period_budget.id}: set to {budget.id}")

            if existing_next_period:
                # 已經生成過該週期的預算，將當前預算標記為非最新
                if budget.is_latest_period:
                    budget.is_latest_period = False
                    logger.info(f"Marked budget '{budget.name}' (ID: {budget.id}) as not latest period")
                continue

            # 創建新的週期預算
            logger.info(f"Creating new period for budget '{budget.name}' (ID: {budget.id}): {next_start} to {next_end}")
            created_count += 1

            # 創建新的週期預算
            new_budget = Budget(
                name=budget.name,
                category=budget.category,
                amount=budget.amount,
                daily_limit=budget.daily_limit,
                spent=0.0,  # 新週期重置為0
                range_mode='recurring',
                period=budget.period,
                start_date=next_start,
                end_date=next_end,
                user_id=budget.user_id,
                parent_budget_id=budget.id,  # 設定父預算
                is_latest_period=True  # 新預算是最新週期
            )

            # 將舊預算標記為非最新週期
            budget.is_latest_period = False

            db.add(new_budget)
            db.flush()  # 取得 new_budget.id

            # 複製帳戶綁定關係
            for account in budget.accounts:
                budget_account = BudgetAccount(
                    budget_id=new_budget.id,
                    account_id=account.id
                )
                db.add(budget_account)

            # 複製類別綁定關係
            old_budget_categories = db.query(BudgetCategory).filter(BudgetCategory.budget_id == budget.id).all()
            # 使用 set 去除重複的類別名稱
            unique_categories = set(bc.category_name for bc in old_budget_categories)
            
            for category_name in unique_categories:
                new_budget_category = BudgetCategory(
                    budget_id=new_budget.id,
                    category_name=category_name
                )
                db.add(new_budget_category)

        db.commit()
        logger.info(f"Successfully created {created_count} recurring budgets (checked {len(budgets_to_renew)} total)")

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating recurring budgets: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 供測試使用
    create_next_period_budgets()
