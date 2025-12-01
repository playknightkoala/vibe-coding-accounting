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

        for budget in budgets_to_renew:
            # 計算下一個週期的時間範圍
            next_start, next_end = calculate_next_period_range(budget.period, budget.end_date)

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
        print(f"Successfully created {len(budgets_to_renew)} recurring budgets")

    except Exception as e:
        db.rollback()
        print(f"Error creating recurring budgets: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 供測試使用
    create_next_period_budgets()
