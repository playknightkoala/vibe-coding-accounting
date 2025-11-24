from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
from datetime import datetime, date
from calendar import monthrange
from app.core.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.transaction import Transaction as TransactionSchema, TransactionCreate, TransactionUpdate, MonthlyStats, DailyStats
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[TransactionSchema])
def get_transactions(
    account_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).join(Account).filter(Account.user_id == current_user.id)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    transactions = query.all()
    return transactions

@router.post("/", response_model=TransactionSchema)
def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)

    # Update account balance
    if transaction.transaction_type == "credit":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/{transaction_id}", response_model=TransactionSchema)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.put("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    old_amount = transaction.amount
    old_type = transaction.transaction_type

    for key, value in transaction_update.dict(exclude_unset=True).items():
        setattr(transaction, key, value)

    # Update account balance if amount changed
    account = transaction.account
    if old_type == "credit":
        account.balance -= old_amount
    else:
        account.balance += old_amount

    if transaction.transaction_type == "credit":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount

    db.commit()
    db.refresh(transaction)
    return transaction

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update account balance
    account = transaction.account
    if transaction.transaction_type == "credit":
        account.balance -= transaction.amount
    else:
        account.balance += transaction.amount

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

@router.get("/stats/monthly", response_model=MonthlyStats)
def get_monthly_stats(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily income and expense statistics for a specific month"""
    # Get the number of days in the month
    _, num_days = monthrange(year, month)

    # Get all user's account IDs
    user_account_ids = db.query(Account.id).filter(Account.user_id == current_user.id).all()
    account_ids = [acc_id for (acc_id,) in user_account_ids]

    if not account_ids:
        # No accounts, return empty stats
        return MonthlyStats(daily_stats=[
            DailyStats(date=f"{year}-{month:02d}-{day:02d}", credit=0.0, debit=0.0)
            for day in range(1, num_days + 1)
        ])

    # Query transactions for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = db.query(
        func.date(Transaction.transaction_date).label('date'),
        Transaction.transaction_type,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date
    ).group_by(
        func.date(Transaction.transaction_date),
        Transaction.transaction_type
    ).all()

    # Build a dictionary for quick lookup
    stats_dict = {}
    for trans in transactions:
        date_str = trans.date.strftime('%Y-%m-%d')
        if date_str not in stats_dict:
            stats_dict[date_str] = {'credit': 0.0, 'debit': 0.0}
        stats_dict[date_str][trans.transaction_type] = float(trans.total)

    # Build the daily stats list with all days in the month
    daily_stats = []
    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        stats = stats_dict.get(date_str, {'credit': 0.0, 'debit': 0.0})
        daily_stats.append(DailyStats(
            date=date_str,
            credit=stats['credit'],
            debit=stats['debit']
        ))

    return MonthlyStats(daily_stats=daily_stats)

@router.get("/stats/daily/{date_str}", response_model=List[TransactionSchema])
def get_daily_transactions(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions for a specific date"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Get all user's account IDs
    user_account_ids = db.query(Account.id).filter(Account.user_id == current_user.id).all()
    account_ids = [acc_id for (acc_id,) in user_account_ids]

    if not account_ids:
        return []

    # Query transactions for the specific date
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())

    transactions = db.query(Transaction).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= start_datetime,
        Transaction.transaction_date <= end_datetime
    ).order_by(Transaction.transaction_date.desc()).all()

    return transactions
@router.get("/descriptions/list", response_model=List[str])
def get_transaction_descriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all distinct transaction descriptions for the current user"""
    descriptions = db.query(Transaction.description).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.description != None,
        Transaction.description != ""
    ).distinct().all()
    
    return [desc[0] for desc in descriptions]
