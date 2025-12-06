from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
from datetime import datetime, date
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import uuid
from app.core.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.transaction import Transaction as TransactionSchema, TransactionCreate, TransactionUpdate, MonthlyStats, DailyStats, TransferCreate
from app.api.deps import get_current_user
from app.core.timezone import from_iso_string, to_utc, to_taipei_time, TAIPEI_TZ

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

    # Handle installment transactions
    if transaction.is_installment and transaction.total_installments and transaction.billing_day:
        return create_installment_transactions(transaction, account, db)

    # Regular transaction
    # 將前端傳來的台北時間轉換為 UTC 儲存
    transaction_data = transaction.dict(exclude={'is_installment', 'total_installments', 'billing_day'})
    if isinstance(transaction_data['transaction_date'], str):
        transaction_data['transaction_date'] = from_iso_string(transaction_data['transaction_date'])
    elif transaction_data['transaction_date']:
        # 如果是 datetime 物件，確保為台北時間
        transaction_data['transaction_date'] = to_utc(transaction_data['transaction_date'])

    db_transaction = Transaction(**transaction_data)
    db.add(db_transaction)

    # Update account balance
    if transaction.transaction_type == "credit":
        account.balance += transaction.amount
    elif transaction.transaction_type in ["debit", "installment"]:
        account.balance -= transaction.amount

    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.post("/transfer", response_model=List[TransactionSchema])
def create_transfer(
    transfer: TransferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a transfer between two accounts.
    Creates two transactions: one 'transfer_out' and one 'transfer_in'.
    """
    # Verify source account
    from_account = db.query(Account).filter(
        Account.id == transfer.from_account_id,
        Account.user_id == current_user.id
    ).first()
    if not from_account:
        raise HTTPException(status_code=404, detail="Source account not found")

    # Verify destination account
    to_account = db.query(Account).filter(
        Account.id == transfer.to_account_id,
        Account.user_id == current_user.id
    ).first()
    if not to_account:
        raise HTTPException(status_code=404, detail="Destination account not found")

    # Check for sufficient funds - REMOVED per user request
    # if from_account.balance < transfer.amount:
    #     raise HTTPException(status_code=400, detail="Insufficient funds in source account")

    # Handle timezone for transaction date
    transaction_date = transfer.transaction_date
    if isinstance(transaction_date, str):
        transaction_date = from_iso_string(transaction_date)
    elif transaction_date:
        transaction_date = to_utc(transaction_date)

    # Generate transfer pair ID to link both transactions
    transfer_pair_id = str(uuid.uuid4())

    # Create 'transfer_out' transaction
    out_transaction = Transaction(
        description=transfer.description,
        amount=transfer.amount,
        transaction_type="transfer_out",
        category="轉帳",
        note=transfer.note,
        transaction_date=transaction_date,
        account_id=from_account.id,
        exclude_from_budget=True,  # Transfers shouldn't affect budget
        transfer_pair_id=transfer_pair_id
    )
    db.add(out_transaction)
    from_account.balance -= transfer.amount

    # Create 'transfer_in' transaction
    in_transaction = Transaction(
        description=transfer.description,
        amount=transfer.amount,
        transaction_type="transfer_in",
        category="轉帳",
        note=transfer.note,
        transaction_date=transaction_date,
        account_id=to_account.id,
        exclude_from_budget=True,  # Transfers shouldn't affect budget
        transfer_pair_id=transfer_pair_id
    )
    db.add(in_transaction)
    to_account.balance += transfer.amount

    db.commit()
    db.refresh(out_transaction)
    db.refresh(in_transaction)

    return [out_transaction, in_transaction]


def create_installment_transactions(
    transaction: TransactionCreate,
    account: Account,
    db: Session
) -> TransactionSchema:
    """Create multiple installment transactions"""
    total_amount = transaction.amount
    num_installments = transaction.total_installments
    billing_day = transaction.billing_day
    annual_rate = transaction.annual_interest_rate or 0

    # Calculate installment amounts
    if annual_rate >= 1:
        # Use loan payment formula: P * r * (1+r)^n / ((1+r)^n - 1)
        # where P = principal, r = monthly rate, n = total periods
        monthly_rate = annual_rate / 12 / 100  # Convert annual % to monthly decimal
        monthly_payment = total_amount * monthly_rate * ((1 + monthly_rate) ** num_installments) / (((1 + monthly_rate) ** num_installments) - 1)
        base_amount = int(monthly_payment)  # Round down to integer

        # Calculate last installment separately to account for rounding
        total_paid_before_last = base_amount * (num_installments - 1)

        # Calculate actual total with interest
        total_with_interest = int(monthly_payment * num_installments)
        last_installment_amount = total_with_interest - total_paid_before_last
        total_interest = total_with_interest - total_amount

        first_installment_amount = base_amount

        # Build note with interest information
        installment_note = f"含利息分期 {num_installments} 期，年利率 {annual_rate}%\n本金：{int(total_amount)} 元\n利息：{total_interest} 元\n總計：{total_with_interest} 元"
        if transaction.note:
            installment_note = f"{transaction.note}\n\n{installment_note}"
    else:
        # Zero-interest: integer division
        base_amount = int(total_amount / num_installments)
        remainder = int(total_amount - (base_amount * num_installments))
        first_installment_amount = base_amount + remainder
        last_installment_amount = base_amount

        # Build note for zero-interest installment
        installment_note = f"零利率分期 {num_installments} 期\n總金額：{int(total_amount)} 元"
        if transaction.note:
            installment_note = f"{transaction.note}\n\n{installment_note}"

    # Generate group ID for all installments
    group_id = str(uuid.uuid4())

    # Parse transaction date
    if isinstance(transaction.transaction_date, str):
        base_date = from_iso_string(transaction.transaction_date)
    else:
        base_date = to_utc(transaction.transaction_date)

    # Calculate first billing date (next month on billing_day)
    first_billing_date = base_date.replace(day=1) + relativedelta(months=1)
    # Adjust to billing day, handling month-end cases
    try:
        first_billing_date = first_billing_date.replace(day=billing_day)
    except ValueError:
        # Day doesn't exist in month (e.g., Feb 30), use last day of month
        last_day = monthrange(first_billing_date.year, first_billing_date.month)[1]
        first_billing_date = first_billing_date.replace(day=last_day)

    created_transactions = []
    first_transaction = None

    for i in range(num_installments):
        # Calculate this installment's amount
        if i == num_installments - 1:
            # Last installment
            installment_amount = last_installment_amount
        elif i == 0 and annual_rate < 1:
            # First installment for zero-interest (includes remainder)
            installment_amount = first_installment_amount
        else:
            # Regular installment
            installment_amount = base_amount

        # Calculate remaining amount AFTER this installment
        if annual_rate >= 1:
            # For interest-bearing, calculate based on total with interest
            total_with_interest = int((total_amount * (annual_rate / 12 / 100) * ((1 + annual_rate / 12 / 100) ** num_installments) / (((1 + annual_rate / 12 / 100) ** num_installments) - 1)) * num_installments)
            paid_so_far = base_amount * (i + 1) if i < num_installments - 1 else total_with_interest
            remaining_after = total_with_interest - paid_so_far
        else:
            # For zero-interest
            remainder = int(total_amount - (base_amount * num_installments))
            paid_so_far = base_amount * (i + 1) + (remainder if i == 0 else 0)
            remaining_after = total_amount - paid_so_far

        # Calculate billing date
        billing_date = first_billing_date + relativedelta(months=i)

        # Adjust for month-end edge cases
        try:
            billing_date = billing_date.replace(day=billing_day)
        except ValueError:
            last_day = monthrange(billing_date.year, billing_date.month)[1]
            billing_date = billing_date.replace(day=last_day)

        # Keep the time from original transaction
        billing_date = billing_date.replace(
            hour=base_date.hour,
            minute=base_date.minute,
            second=base_date.second
        )

        # Create installment transaction
        db_transaction = Transaction(
            description=transaction.description,
            amount=installment_amount,
            transaction_type="installment",
            category=transaction.category,
            note=installment_note,
            foreign_amount=transaction.foreign_amount,
            foreign_currency=transaction.foreign_currency,
            transaction_date=billing_date,
            account_id=transaction.account_id,
            is_installment=True,
            installment_group_id=group_id,
            installment_number=i + 1,
            total_installments=num_installments,
            total_amount=total_amount,
            remaining_amount=remaining_after,
            annual_interest_rate=annual_rate if annual_rate >= 1 else None,
            exclude_from_budget=transaction.exclude_from_budget
        )

        db.add(db_transaction)
        created_transactions.append(db_transaction)

        if i == 0:
            first_transaction = db_transaction

    # Update account balance (deduct total installment amount including interest)
    if annual_rate >= 1:
        monthly_rate = annual_rate / 12 / 100
        monthly_payment = total_amount * monthly_rate * ((1 + monthly_rate) ** num_installments) / (((1 + monthly_rate) ** num_installments) - 1)
        total_with_interest = int(monthly_payment * num_installments)
        account.balance -= total_with_interest
    else:
        account.balance -= total_amount

    db.commit()

    # Refresh and return first transaction
    if first_transaction:
        db.refresh(first_transaction)
        return first_transaction

    raise HTTPException(status_code=500, detail="Failed to create installments")

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

    update_data = transaction_update.dict(exclude_unset=True)

    # 處理交易時間的時區轉換
    if 'transaction_date' in update_data and update_data['transaction_date']:
        if isinstance(update_data['transaction_date'], str):
            update_data['transaction_date'] = from_iso_string(update_data['transaction_date'])
        else:
            update_data['transaction_date'] = to_utc(update_data['transaction_date'])

    for key, value in update_data.items():
        setattr(transaction, key, value)

    # Update account balance if amount changed
    account = transaction.account
    
    # Revert old balance change
    if old_type == "credit" or old_type == "transfer_in":
        account.balance -= old_amount
    elif old_type in ["debit", "installment", "transfer_out"]:
        account.balance += old_amount

    # Apply new balance change
    if transaction.transaction_type == "credit" or transaction.transaction_type == "transfer_in":
        account.balance += transaction.amount
    elif transaction.transaction_type in ["debit", "installment", "transfer_out"]:
        account.balance -= transaction.amount

    # 連動更新配對交易（轉帳）
    if transaction.transfer_pair_id:
        pair_transaction = db.query(Transaction).join(Account).filter(
            Transaction.transfer_pair_id == transaction.transfer_pair_id,
            Transaction.id != transaction.id,
            Account.user_id == current_user.id
        ).first()
        
        if pair_transaction:
            pair_old_amount = pair_transaction.amount
            pair_old_type = pair_transaction.transaction_type
            pair_account = pair_transaction.account
            
            # Revert old balance on pair account
            if pair_old_type == "credit" or pair_old_type == "transfer_in":
                pair_account.balance -= pair_old_amount
            elif pair_old_type in ["debit", "installment", "transfer_out"]:
                pair_account.balance += pair_old_amount
            
            # Update pair transaction with synced fields
            pair_transaction.amount = transaction.amount
            pair_transaction.description = transaction.description
            pair_transaction.note = transaction.note
            if 'transaction_date' in update_data:
                pair_transaction.transaction_date = update_data['transaction_date']
            
            # Apply new balance on pair account
            if pair_transaction.transaction_type == "credit" or pair_transaction.transaction_type == "transfer_in":
                pair_account.balance += pair_transaction.amount
            elif pair_transaction.transaction_type in ["debit", "installment", "transfer_out"]:
                pair_account.balance -= pair_transaction.amount

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
    if transaction.transaction_type == "credit" or transaction.transaction_type == "transfer_in":
        account.balance -= transaction.amount
    elif transaction.transaction_type in ["debit", "installment", "transfer_out"]:
        account.balance += transaction.amount

    # 連動刪除配對交易（轉帳）
    deleted_pair = False
    if transaction.transfer_pair_id:
        pair_transaction = db.query(Transaction).join(Account).filter(
            Transaction.transfer_pair_id == transaction.transfer_pair_id,
            Transaction.id != transaction.id,
            Account.user_id == current_user.id
        ).first()
        
        if pair_transaction:
            pair_account = pair_transaction.account
            
            # Update pair account balance
            if pair_transaction.transaction_type == "credit" or pair_transaction.transaction_type == "transfer_in":
                pair_account.balance -= pair_transaction.amount
            elif pair_transaction.transaction_type in ["debit", "installment", "transfer_out"]:
                pair_account.balance += pair_transaction.amount
            
            db.delete(pair_transaction)
            deleted_pair = True

    db.delete(transaction)
    db.commit()
    
    if deleted_pair:
        return {"message": "Transfer transactions deleted successfully (both transfer_out and transfer_in)"}
    return {"message": "Transaction deleted successfully"}


@router.delete("/installments/group/{group_id}")
def delete_installment_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all transactions in an installment group"""
    # Get all transactions in the group
    transactions = db.query(Transaction).join(Account).filter(
        Transaction.installment_group_id == group_id,
        Account.user_id == current_user.id
    ).all()

    if not transactions:
        raise HTTPException(status_code=404, detail="Installment group not found")

    # Update account balance by reversing all installment amounts
    account = transactions[0].account
    total_to_reverse = sum(t.amount for t in transactions)
    account.balance += total_to_reverse

    # Delete all transactions
    for transaction in transactions:
        db.delete(transaction)

    db.commit()
    return {"message": f"Deleted {len(transactions)} installment transactions successfully"}

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
