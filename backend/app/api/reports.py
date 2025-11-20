from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date
from calendar import monthrange
from collections import defaultdict

from app.core.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.report import (
    OverviewReport, DetailsReport, CategoryReport,
    RankingReport, AccountReport, CategoryStats,
    AccountStats, TransactionDetail, DailyTransactions
)
from app.api.deps import get_current_user

router = APIRouter()

def get_user_transactions(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    """Helper function to get user's transactions within date range"""
    user_account_ids = db.query(Account.id).filter(Account.user_id == user_id).all()
    account_ids = [acc_id for (acc_id,) in user_account_ids]

    if not account_ids:
        return []

    transactions = db.query(Transaction, Account).join(
        Account, Transaction.account_id == Account.id
    ).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date
    ).order_by(Transaction.transaction_date.desc()).all()

    return [
        TransactionDetail(
            id=trans.id,
            description=trans.description,
            amount=trans.amount,
            transaction_type=trans.transaction_type,
            category=trans.category,
            transaction_date=trans.transaction_date,
            account_id=trans.account_id,
            account_name=account.name
        )
        for trans, account in transactions
    ]

@router.get("/overview/monthly", response_model=OverviewReport)
def get_monthly_overview(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly overview report"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Calculate totals
    total_credit = sum(t.amount for t in transactions if t.transaction_type == 'credit')
    total_debit = sum(t.amount for t in transactions if t.transaction_type == 'debit')
    net_amount = total_credit - total_debit

    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        else:
            category_totals[cat]['debit'] += t.amount

    total_amount = total_debit  # Use debit for percentage calculation
    category_stats = []
    for cat, amounts in category_totals.items():
        amount = amounts['debit']
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        category_stats.append(CategoryStats(
            category=cat,
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit']
        ))

    category_stats.sort(key=lambda x: x.amount, reverse=True)

    # Get top 5 transactions
    top_five_income = sorted(
        [t for t in transactions if t.transaction_type == 'credit'],
        key=lambda x: x.amount,
        reverse=True
    )[:5]

    top_five_expense = sorted(
        [t for t in transactions if t.transaction_type == 'debit'],
        key=lambda x: x.amount,
        reverse=True
    )[:5]

    return OverviewReport(
        total_credit=total_credit,
        total_debit=total_debit,
        net_amount=net_amount,
        category_stats=category_stats,
        top_five_income=top_five_income,
        top_five_expense=top_five_expense
    )

@router.get("/overview/daily", response_model=OverviewReport)
def get_daily_overview(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily overview report"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Calculate totals
    total_credit = sum(t.amount for t in transactions if t.transaction_type == 'credit')
    total_debit = sum(t.amount for t in transactions if t.transaction_type == 'debit')
    net_amount = total_credit - total_debit

    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        else:
            category_totals[cat]['debit'] += t.amount

    total_amount = total_debit
    category_stats = []
    for cat, amounts in category_totals.items():
        amount = amounts['debit']
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        category_stats.append(CategoryStats(
            category=cat,
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit']
        ))

    category_stats.sort(key=lambda x: x.amount, reverse=True)

    # Get top 5 transactions
    top_five_income = sorted(
        [t for t in transactions if t.transaction_type == 'credit'],
        key=lambda x: x.amount,
        reverse=True
    )[:5]

    top_five_expense = sorted(
        [t for t in transactions if t.transaction_type == 'debit'],
        key=lambda x: x.amount,
        reverse=True
    )[:5]

    return OverviewReport(
        total_credit=total_credit,
        total_debit=total_debit,
        net_amount=net_amount,
        category_stats=category_stats,
        top_five_income=top_five_income,
        top_five_expense=top_five_expense
    )

@router.get("/details/monthly", response_model=DetailsReport)
def get_monthly_details(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly details report"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Group by date
    daily_groups = defaultdict(list)
    for t in transactions:
        date_str = t.transaction_date.strftime('%Y-%m-%d')
        daily_groups[date_str].append(t)

    # Create daily transactions
    daily_transactions = []
    for date_str in sorted(daily_groups.keys(), reverse=True):
        day_trans = daily_groups[date_str]
        total_credit = sum(t.amount for t in day_trans if t.transaction_type == 'credit')
        total_debit = sum(t.amount for t in day_trans if t.transaction_type == 'debit')

        daily_transactions.append(DailyTransactions(
            date=date_str,
            total_credit=total_credit,
            total_debit=total_debit,
            transactions=sorted(day_trans, key=lambda x: x.transaction_date, reverse=True)
        ))

    total_credit = sum(t.amount for t in transactions if t.transaction_type == 'credit')
    total_debit = sum(t.amount for t in transactions if t.transaction_type == 'debit')

    return DetailsReport(
        daily_transactions=daily_transactions,
        total_credit=total_credit,
        total_debit=total_debit
    )

@router.get("/details/daily", response_model=DetailsReport)
def get_daily_details(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily details report"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    total_credit = sum(t.amount for t in transactions if t.transaction_type == 'credit')
    total_debit = sum(t.amount for t in transactions if t.transaction_type == 'debit')

    daily_transactions = [DailyTransactions(
        date=date_str,
        total_credit=total_credit,
        total_debit=total_debit,
        transactions=sorted(transactions, key=lambda x: x.transaction_date, reverse=True)
    )]

    return DetailsReport(
        daily_transactions=daily_transactions,
        total_credit=total_credit,
        total_debit=total_debit
    )

@router.get("/category/monthly", response_model=CategoryReport)
def get_monthly_category_report(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly category report"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        else:
            category_totals[cat]['debit'] += t.amount

    total_amount = sum(amounts['debit'] for amounts in category_totals.values())

    category_stats = []
    for cat, amounts in category_totals.items():
        amount = amounts['debit']
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        category_stats.append(CategoryStats(
            category=cat,
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit']
        ))

    category_stats.sort(key=lambda x: x.amount, reverse=True)

    return CategoryReport(
        category_stats=category_stats,
        total_amount=total_amount
    )

@router.get("/category/daily", response_model=CategoryReport)
def get_daily_category_report(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily category report"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        else:
            category_totals[cat]['debit'] += t.amount

    total_amount = sum(amounts['debit'] for amounts in category_totals.values())

    category_stats = []
    for cat, amounts in category_totals.items():
        amount = amounts['debit']
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        category_stats.append(CategoryStats(
            category=cat,
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit']
        ))

    category_stats.sort(key=lambda x: x.amount, reverse=True)

    return CategoryReport(
        category_stats=category_stats,
        total_amount=total_amount
    )

@router.get("/ranking/monthly", response_model=RankingReport)
def get_monthly_ranking(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly ranking report"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    expense_ranking = sorted(
        [t for t in transactions if t.transaction_type == 'debit'],
        key=lambda x: x.amount,
        reverse=True
    )

    income_ranking = sorted(
        [t for t in transactions if t.transaction_type == 'credit'],
        key=lambda x: x.amount,
        reverse=True
    )

    return RankingReport(
        expense_ranking=expense_ranking,
        income_ranking=income_ranking
    )

@router.get("/ranking/daily", response_model=RankingReport)
def get_daily_ranking(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily ranking report"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    expense_ranking = sorted(
        [t for t in transactions if t.transaction_type == 'debit'],
        key=lambda x: x.amount,
        reverse=True
    )

    income_ranking = sorted(
        [t for t in transactions if t.transaction_type == 'credit'],
        key=lambda x: x.amount,
        reverse=True
    )

    return RankingReport(
        expense_ranking=expense_ranking,
        income_ranking=income_ranking
    )

@router.get("/account/monthly", response_model=AccountReport)
def get_monthly_account_report(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly account report"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Get all user accounts
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    account_map = {acc.id: acc.name for acc in accounts}

    # Calculate account stats
    account_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        if t.transaction_type == 'credit':
            account_totals[t.account_id]['credit'] += t.amount
        else:
            account_totals[t.account_id]['debit'] += t.amount

    total_amount = sum(amounts['debit'] for amounts in account_totals.values())

    account_stats = []
    for acc_id, amounts in account_totals.items():
        amount = amounts['debit']
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        balance = amounts['credit'] - amounts['debit']

        account_stats.append(AccountStats(
            account_id=acc_id,
            account_name=account_map.get(acc_id, '未知帳戶'),
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit'],
            balance=balance
        ))

    account_stats.sort(key=lambda x: x.amount, reverse=True)

    return AccountReport(
        account_stats=account_stats,
        total_amount=total_amount
    )

@router.get("/account/daily", response_model=AccountReport)
def get_daily_account_report(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily account report"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Get all user accounts
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    account_map = {acc.id: acc.name for acc in accounts}

    # Calculate account stats
    account_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        if t.transaction_type == 'credit':
            account_totals[t.account_id]['credit'] += t.amount
        else:
            account_totals[t.account_id]['debit'] += t.amount

    total_amount = sum(amounts['debit'] for amounts in account_totals.values())

    account_stats = []
    for acc_id, amounts in account_totals.items():
        amount = amounts['debit']
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        balance = amounts['credit'] - amounts['debit']

        account_stats.append(AccountStats(
            account_id=acc_id,
            account_name=account_map.get(acc_id, '未知帳戶'),
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit'],
            balance=balance
        ))

    account_stats.sort(key=lambda x: x.amount, reverse=True)

    return AccountReport(
        account_stats=account_stats,
        total_amount=total_amount
    )

# Get category transactions
@router.get("/category/{category}/transactions/monthly")
def get_category_transactions_monthly(
    category: str,
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific category in a month"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Filter by category
    cat_name = None if category == '未分類' else category
    filtered = [t for t in transactions if t.category == cat_name]

    return filtered

@router.get("/category/{category}/transactions/daily")
def get_category_transactions_daily(
    category: str,
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific category on a specific day"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Filter by category
    cat_name = None if category == '未分類' else category
    filtered = [t for t in transactions if t.category == cat_name]

    return filtered

# Get account transactions
@router.get("/account/{account_id}/transactions/monthly")
def get_account_transactions_monthly(
    account_id: int,
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific account in a month"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Filter by account
    filtered = [t for t in transactions if t.account_id == account_id]

    return filtered

@router.get("/account/{account_id}/transactions/daily")
def get_account_transactions_daily(
    account_id: int,
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific account on a specific day"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)

    # Filter by account
    filtered = [t for t in transactions if t.account_id == account_id]

    return filtered
