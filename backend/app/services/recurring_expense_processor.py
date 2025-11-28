"""
固定支出處理服務

此服務負責：
1. 檢查所有啟用的固定支出
2. 判斷哪些固定支出需要建立新的交易
3. 建立到期的固定支出交易
4. 更新帳戶餘額
"""

from sqlalchemy.orm import Session
from datetime import datetime
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import logging

from app.models.recurring_expense import RecurringExpense
from app.models.transaction import Transaction
from app.core.timezone import to_utc, TAIPEI_TZ

logger = logging.getLogger(__name__)

def process_recurring_expenses(db: Session):
    """
    處理所有到期的固定支出

    執行邏輯：
    1. 查詢所有啟用的固定支出
    2. 對每個固定支出，檢查是否需要建立新交易
    3. 建立交易並更新帳戶餘額
    4. 更新 last_executed_date
    """
    logger.info("Starting recurring expense processing")

    # Get current time in Taipei timezone
    now = datetime.now(TAIPEI_TZ)
    today = now.date()

    # Query all active recurring expenses
    recurring_expenses = db.query(RecurringExpense).filter(
        RecurringExpense.is_active == True
    ).all()

    logger.info(f"Found {len(recurring_expenses)} active recurring expenses")

    transactions_created = 0

    for recurring_expense in recurring_expenses:
        try:
            # Check if end_date has passed
            if recurring_expense.end_date:
                end_date_local = recurring_expense.end_date.astimezone(TAIPEI_TZ).date()
                if today > end_date_local:
                    logger.info(f"Recurring expense {recurring_expense.id} has ended, skipping")
                    continue

            # Calculate the target date for this month
            target_date = calculate_target_date(today, recurring_expense.day_of_month)

            # Check if we need to create a transaction
            if should_create_transaction(recurring_expense, target_date, today):
                # Create transaction
                transaction = create_recurring_transaction(
                    db=db,
                    recurring_expense=recurring_expense,
                    target_date=target_date
                )

                if transaction:
                    # Update account balance
                    account = recurring_expense.account
                    account.balance -= recurring_expense.amount

                    # Update last_executed_date
                    recurring_expense.last_executed_date = to_utc(datetime.combine(target_date, datetime.min.time()).replace(tzinfo=TAIPEI_TZ))

                    transactions_created += 1
                    logger.info(f"Created transaction for recurring expense {recurring_expense.id}")

        except Exception as e:
            logger.error(f"Failed to process recurring expense {recurring_expense.id}: {e}")
            continue

    # Commit all changes
    db.commit()

    logger.info(f"Recurring expense processing complete. Created {transactions_created} transactions")
    return transactions_created

def calculate_target_date(today, day_of_month):
    """
    計算目標日期（本月的指定日期）

    處理月底邊界情況（例如 2月30日 → 2月28日或29日）
    """
    try:
        target_date = today.replace(day=day_of_month)
    except ValueError:
        # Day doesn't exist in this month (e.g., Feb 30)
        last_day = monthrange(today.year, today.month)[1]
        target_date = today.replace(day=last_day)

    return target_date

def should_create_transaction(recurring_expense, target_date, today):
    """
    判斷是否應該建立交易

    條件：
    1. 目標日期已到達（今天 >= 目標日期）
    2. 尚未執行過，或上次執行日期不是本月
    """
    # Check if target date has arrived
    if today < target_date:
        return False

    # Check if already executed this month
    if recurring_expense.last_executed_date:
        last_executed_local = recurring_expense.last_executed_date.astimezone(TAIPEI_TZ).date()

        # If last executed in the same month and year, skip
        if (last_executed_local.year == target_date.year and
            last_executed_local.month == target_date.month):
            return False

    return True

def create_recurring_transaction(db: Session, recurring_expense: RecurringExpense, target_date):
    """
    建立固定支出的交易記錄

    交易日期設為目標日期的當天開始時間
    """
    # Create datetime for the transaction (midnight of target date)
    transaction_datetime = datetime.combine(
        target_date,
        datetime.min.time()
    ).replace(tzinfo=TAIPEI_TZ)

    # Build note with recurring expense information
    recurring_note = f"固定支出 - 每月 {recurring_expense.day_of_month} 號"
    if recurring_expense.note:
        recurring_note = f"{recurring_expense.note}\n\n{recurring_note}"

    # Create transaction
    transaction = Transaction(
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        transaction_type="debit",
        category=recurring_expense.category,
        note=recurring_note,
        transaction_date=to_utc(transaction_datetime),
        account_id=recurring_expense.account_id,
        recurring_group_id=recurring_expense.recurring_group_id,
        is_from_recurring=True
    )

    db.add(transaction)

    return transaction
