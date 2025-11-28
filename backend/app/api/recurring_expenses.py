from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.recurring_expense import RecurringExpense
from app.models.transaction import Transaction
from app.schemas.recurring_expense import RecurringExpense as RecurringExpenseSchema, RecurringExpenseCreate, RecurringExpenseUpdate
from app.api.deps import get_current_user
from app.core.timezone import to_utc, TAIPEI_TZ

router = APIRouter()

@router.get("/", response_model=List[RecurringExpenseSchema])
def get_recurring_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得目前使用者的所有固定支出"""
    # Get all user's account IDs
    user_account_ids = db.query(Account.id).filter(Account.user_id == current_user.id).all()
    account_ids = [acc_id for (acc_id,) in user_account_ids]

    if not account_ids:
        return []

    # Query recurring expenses for user's accounts
    recurring_expenses = db.query(RecurringExpense).filter(
        RecurringExpense.account_id.in_(account_ids)
    ).all()

    return recurring_expenses

@router.post("/", response_model=RecurringExpenseSchema)
def create_recurring_expense(
    recurring_expense: RecurringExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """建立新的固定支出"""
    # Verify account belongs to user
    account = db.query(Account).filter(
        Account.id == recurring_expense.account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Generate UUID for recurring group
    recurring_group_id = str(uuid.uuid4())

    # Calculate start_date (next occurrence of day_of_month from today)
    now = datetime.now(TAIPEI_TZ)
    today = now.date()

    # Try current month first
    try:
        start_date = datetime(today.year, today.month, recurring_expense.day_of_month, tzinfo=TAIPEI_TZ)
    except ValueError:
        # Day doesn't exist in current month (e.g., Feb 30), use last day
        last_day = monthrange(today.year, today.month)[1]
        start_date = datetime(today.year, today.month, last_day, tzinfo=TAIPEI_TZ)

    # If start_date is in the past, move to next month
    if start_date.date() < today:
        next_month = start_date + relativedelta(months=1)
        try:
            start_date = next_month.replace(day=recurring_expense.day_of_month)
        except ValueError:
            last_day = monthrange(next_month.year, next_month.month)[1]
            start_date = next_month.replace(day=last_day)

    # Create recurring expense
    db_recurring_expense = RecurringExpense(
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        category=recurring_expense.category,
        note=recurring_expense.note,
        day_of_month=recurring_expense.day_of_month,
        account_id=recurring_expense.account_id,
        recurring_group_id=recurring_group_id,
        start_date=to_utc(start_date),
        is_active=True
    )

    db.add(db_recurring_expense)
    db.commit()
    db.refresh(db_recurring_expense)

    return db_recurring_expense

@router.put("/{recurring_expense_id}", response_model=RecurringExpenseSchema)
def update_recurring_expense(
    recurring_expense_id: int,
    recurring_expense_update: RecurringExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新固定支出"""
    # Get recurring expense and verify ownership
    recurring_expense = db.query(RecurringExpense).join(Account).filter(
        RecurringExpense.id == recurring_expense_id,
        Account.user_id == current_user.id
    ).first()

    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    # Update fields
    update_data = recurring_expense_update.dict(exclude_unset=True)

    # Convert end_date to UTC if provided
    if 'end_date' in update_data and update_data['end_date']:
        update_data['end_date'] = to_utc(update_data['end_date'])

    for key, value in update_data.items():
        setattr(recurring_expense, key, value)

    db.commit()
    db.refresh(recurring_expense)

    return recurring_expense

@router.delete("/{recurring_expense_id}")
def delete_recurring_expense(
    recurring_expense_id: int,
    mode: str = Query(..., description="Delete mode: 'single', 'future', 'all'"),
    transaction_id: int = Query(None, description="Transaction ID (required for 'single' and 'future' modes)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刪除固定支出

    三種刪除模式:
    - single: 刪除單筆交易 (需提供 transaction_id)
    - future: 刪除此筆交易及之後的所有交易 (需提供 transaction_id)
    - all: 刪除這個固定支出的所有交易和固定支出本身
    """
    # Get recurring expense and verify ownership
    recurring_expense = db.query(RecurringExpense).join(Account).filter(
        RecurringExpense.id == recurring_expense_id,
        Account.user_id == current_user.id
    ).first()

    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    recurring_group_id = recurring_expense.recurring_group_id

    if mode == "single":
        # 刪除單筆交易
        if not transaction_id:
            raise HTTPException(status_code=400, detail="transaction_id is required for 'single' mode")

        transaction = db.query(Transaction).join(Account).filter(
            Transaction.id == transaction_id,
            Transaction.recurring_group_id == recurring_group_id,
            Account.user_id == current_user.id
        ).first()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Update account balance only if transaction date has passed
        now = datetime.now(TAIPEI_TZ)
        if transaction.transaction_date <= to_utc(now):
            account = transaction.account
            # Reverse the debit transaction
            account.balance += transaction.amount

        db.delete(transaction)
        db.commit()

        return {"message": "Transaction deleted successfully"}

    elif mode == "future":
        # 刪除此筆交易及之後的所有交易
        if not transaction_id:
            raise HTTPException(status_code=400, detail="transaction_id is required for 'future' mode")

        # Get the target transaction
        target_transaction = db.query(Transaction).join(Account).filter(
            Transaction.id == transaction_id,
            Transaction.recurring_group_id == recurring_group_id,
            Account.user_id == current_user.id
        ).first()

        if not target_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        target_date = target_transaction.transaction_date

        # Get all transactions from this date onwards
        transactions = db.query(Transaction).join(Account).filter(
            Transaction.recurring_group_id == recurring_group_id,
            Transaction.transaction_date >= target_date,
            Account.user_id == current_user.id
        ).all()

        # Update account balances for transactions that have already occurred
        now = datetime.now(TAIPEI_TZ)
        now_utc = to_utc(now)

        for transaction in transactions:
            if transaction.transaction_date <= now_utc:
                # Reverse the debit transaction
                transaction.account.balance += transaction.amount
            db.delete(transaction)

        # Set end_date on recurring expense to prevent future transactions
        recurring_expense.end_date = target_date
        recurring_expense.is_active = False

        db.commit()

        return {"message": f"Deleted {len(transactions)} transactions and stopped recurring expense"}

    elif mode == "all":
        # 刪除所有交易和固定支出本身
        transactions = db.query(Transaction).join(Account).filter(
            Transaction.recurring_group_id == recurring_group_id,
            Account.user_id == current_user.id
        ).all()

        # Update account balances for transactions that have already occurred
        now = datetime.now(TAIPEI_TZ)
        now_utc = to_utc(now)

        for transaction in transactions:
            if transaction.transaction_date <= now_utc:
                # Reverse the debit transaction
                transaction.account.balance += transaction.amount
            db.delete(transaction)

        # Delete the recurring expense itself
        db.delete(recurring_expense)
        db.commit()

        return {"message": f"Deleted {len(transactions)} transactions and recurring expense"}

    else:
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'single', 'future', or 'all'")

@router.get("/{recurring_expense_id}", response_model=RecurringExpenseSchema)
def get_recurring_expense(
    recurring_expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得單一固定支出"""
    recurring_expense = db.query(RecurringExpense).join(Account).filter(
        RecurringExpense.id == recurring_expense_id,
        Account.user_id == current_user.id
    ).first()

    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    return recurring_expense
