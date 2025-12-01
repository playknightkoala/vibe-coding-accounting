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
from app.schemas.budget_report import BudgetReport, BudgetStats, BudgetTransaction
from app.models.budget import Budget
from app.models.budget_category import BudgetCategory

router = APIRouter()

@router.get("/budget/monthly", response_model=BudgetReport)
def get_monthly_budget_report(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly budget report"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # 1. Get all budgets active in this period
    # For simplicity, we check if the budget overlaps with the requested month
    # And belongs to the user
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.start_date < end_date,
        Budget.end_date >= start_date
    ).all()

    total_budget_amount = sum(b.amount for b in budgets)
    
    # 2. Get transactions that match these budgets
    # We need to filter transactions that fall into any of the budget categories
    # OR if the budget is not category-specific (global budget), include all expenses?
    # Usually budgets are category specific. If category is None, maybe it means all?
    # Let's assume budgets are either category-based or global.
    
    budget_categories = set()
    has_global_budget = False
    
    budget_categories = set()
    has_global_budget = False
    
    for b in budgets:
        # Fetch categories from BudgetCategory table
        cats = db.query(BudgetCategory.category_name).filter(BudgetCategory.budget_id == b.id).all()
        cat_names = [c[0] for c in cats]
        
        if cat_names:
            budget_categories.update(cat_names)
        elif b.category:
            # Fallback to legacy field
            budget_categories.add(b.category)
        else:
            # No categories defined = Global budget
            has_global_budget = True
            
    transactions = get_user_transactions(db, current_user.id, start_date, end_date)
    
    budget_transactions = []
    total_spent = 0.0
    
    for t in transactions:
        # Only consider expenses
        if t.transaction_type not in ['debit', 'installment']:
            continue
            
        # Skip transactions excluded from budget
        if t.exclude_from_budget:
            continue
            
        # Check if transaction matches any budget
        is_included = False
        if has_global_budget:
            is_included = True
        elif t.category in budget_categories:
            is_included = True
            
        if is_included:
            total_spent += t.amount
            budget_transactions.append(BudgetTransaction(
                id=t.id,
                description=t.description,
                amount=t.amount,
                transaction_type=t.transaction_type,
                category=t.category,
                transaction_date=t.transaction_date,
                account_name=t.account_name
            ))
            
    remaining = total_budget_amount - total_spent
    
    # Calculate daily average
    days_in_month = monthrange(year, month)[1]
    current_day = datetime.now().day if datetime.now().year == year and datetime.now().month == month else days_in_month
    daily_average = total_spent / current_day if current_day > 0 else 0
    
    # Projected spending (simple linear projection)
    if datetime.now().year == year and datetime.now().month == month:
        projected_spending = (total_spent / current_day) * days_in_month if current_day > 0 else 0
    else:
        projected_spending = total_spent

    print(f"DEBUG: Year={year}, Month={month}, Spent={total_spent}, Budget={total_budget_amount}, Projected={projected_spending}")

    status = 'on_track'
    usage_percent = total_spent / total_budget_amount if total_budget_amount > 0 else 0
    
    if total_spent > total_budget_amount:
        status = 'over_budget'
    elif usage_percent > 0.8:
        status = 'warning'
    
    # Remove projection-based warning as it confuses users early in the month
    # elif projected_spending > total_budget_amount:
    #     status = 'warning' # Projected to overspend
    
    print(f"DEBUG: Status={status}")
        
    return BudgetReport(
        stats=BudgetStats(
            total_budget=total_budget_amount,
            total_spent=total_spent,
            remaining=remaining,
            daily_average=daily_average,
            projected_spending=projected_spending,
            status=status
        ),
        transactions=budget_transactions
    )

@router.get("/budget/daily", response_model=BudgetReport)
def get_daily_budget_report(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily budget report"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())

    # 1. Get budgets active on this day
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.start_date <= end_date,
        Budget.end_date >= start_date
    ).all()

    # For daily report, we should probably use daily_limit if available, 
    # or prorate the monthly budget? 
    # The requirement says "calculate average daily spend", so maybe we just show 
    # the daily portion of the budget?
    # Let's use daily_limit if set, otherwise prorate amount / days_in_period
    
    total_daily_budget = 0.0
    
    for b in budgets:
        if b.daily_limit:
            total_daily_budget += b.daily_limit
        else:
            # Calculate days in budget period
            period_days = (b.end_date - b.start_date).days + 1
            if period_days > 0:
                total_daily_budget += b.amount / period_days
    
    budget_categories = set()
    has_global_budget = False
    
    budget_categories = set()
    has_global_budget = False
    
    for b in budgets:
        # Fetch categories from BudgetCategory table
        cats = db.query(BudgetCategory.category_name).filter(BudgetCategory.budget_id == b.id).all()
        cat_names = [c[0] for c in cats]
        
        if cat_names:
            budget_categories.update(cat_names)
        elif b.category:
            # Fallback to legacy field
            budget_categories.add(b.category)
        else:
            # No categories defined = Global budget
            has_global_budget = True

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)
    
    budget_transactions = []
    total_spent = 0.0
    
    for t in transactions:
        if t.transaction_type not in ['debit', 'installment']:
            continue
            
        if t.exclude_from_budget:
            continue
            
        is_included = False
        if has_global_budget:
            is_included = True
        elif t.category in budget_categories:
            is_included = True
            
        if is_included:
            total_spent += t.amount
            budget_transactions.append(BudgetTransaction(
                id=t.id,
                description=t.description,
                amount=t.amount,
                transaction_type=t.transaction_type,
                category=t.category,
                transaction_date=t.transaction_date,
                account_name=t.account.name if t.account else "Unknown"
            ))

    remaining = total_daily_budget - total_spent
    
    status = 'on_track'
    if total_spent > total_daily_budget:
        status = 'over_budget'
        
    return BudgetReport(
        stats=BudgetStats(
            total_budget=total_daily_budget,
            total_spent=total_spent,
            remaining=remaining,
            daily_average=total_spent, # For daily, average is just the total
            projected_spending=total_spent, # No projection for daily
            status=status
        ),
        transactions=budget_transactions
    )

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
            account_name=account.name,
            exclude_from_budget=trans.exclude_from_budget
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
    total_debit = sum(t.amount for t in transactions if t.transaction_type in ['debit', 'installment'])
    net_amount = total_credit - total_debit

    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
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
        [t for t in transactions if t.transaction_type in ['debit', 'installment']],
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
    total_debit = sum(t.amount for t in transactions if t.transaction_type in ['debit', 'installment'])
    net_amount = total_credit - total_debit

    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
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
        [t for t in transactions if t.transaction_type in ['debit', 'installment']],
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
    total_debit = sum(t.amount for t in transactions if t.transaction_type in ['debit', 'installment'])

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
    total_debit = sum(t.amount for t in transactions if t.transaction_type in ['debit', 'installment'])

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
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
            category_totals[cat]['debit'] += t.amount

    total_debit = sum(amounts['debit'] for amounts in category_totals.values())
    total_credit = sum(amounts['credit'] for amounts in category_totals.values())

    category_stats = []
    for cat, amounts in category_totals.items():
        # Use debit amount for main sorting and percentage (backward compatible)
        amount = amounts['debit']
        percentage = (amount / total_debit * 100) if total_debit > 0 else 0
        category_stats.append(CategoryStats(
            category=cat,
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit']
        ))

    # Sort by total amount (debit + credit) to show most active categories first
    category_stats.sort(key=lambda x: x.debit + x.credit, reverse=True)

    return CategoryReport(
        category_stats=category_stats,
        total_amount=total_debit,  # Backward compatible
        total_credit=total_credit,
        total_debit=total_debit
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
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
            category_totals[cat]['debit'] += t.amount

    total_debit = sum(amounts['debit'] for amounts in category_totals.values())
    total_credit = sum(amounts['credit'] for amounts in category_totals.values())

    category_stats = []
    for cat, amounts in category_totals.items():
        # Use debit amount for main sorting and percentage (backward compatible)
        amount = amounts['debit']
        percentage = (amount / total_debit * 100) if total_debit > 0 else 0
        category_stats.append(CategoryStats(
            category=cat,
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit']
        ))

    # Sort by total amount (debit + credit) to show most active categories first
    category_stats.sort(key=lambda x: x.debit + x.credit, reverse=True)

    return CategoryReport(
        category_stats=category_stats,
        total_amount=total_debit,  # Backward compatible
        total_credit=total_credit,
        total_debit=total_debit
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
        [t for t in transactions if t.transaction_type in ['debit', 'installment']],
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
        [t for t in transactions if t.transaction_type in ['debit', 'installment']],
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
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        if t.transaction_type == 'credit':
            account_totals[t.account_id]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
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
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        if t.transaction_type == 'credit':
            account_totals[t.account_id]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
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

# Custom date range report endpoints

@router.get("/custom/overview", response_model=OverviewReport)
def get_custom_overview(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get custom date range overview report"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        # Set end to end of day
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    
    # Calculate totals
    total_credit = sum(t.amount for t in transactions if t.transaction_type == 'credit')
    total_debit = sum(t.amount for t in transactions if t.transaction_type in ['debit', 'installment'])
    net_amount = total_credit - total_debit
    
    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
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
        [t for t in transactions if t.transaction_type in ['debit', 'installment']],
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


@router.get("/custom/details", response_model=DetailsReport)
def get_custom_details(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get custom date range details report"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    
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
    total_debit = sum(t.amount for t in transactions if t.transaction_type in ['debit', 'installment'])

    return DetailsReport(
        daily_transactions=daily_transactions,
        total_credit=total_credit,
        total_debit=total_debit
    )


@router.get("/custom/category", response_model=CategoryReport)
def get_custom_category_report(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get custom date range category report"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    
    # Calculate category stats
    category_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        cat = t.category or '未分類'
        if t.transaction_type == 'credit':
            category_totals[cat]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
            category_totals[cat]['debit'] += t.amount

    total_debit = sum(amounts['debit'] for amounts in category_totals.values())
    total_credit = sum(amounts['credit'] for amounts in category_totals.values())

    category_stats = []
    for cat, amounts in category_totals.items():
        # Use debit amount for main sorting and percentage
        amount = amounts['debit']
        percentage = (amount / total_debit * 100) if total_debit > 0 else 0
        category_stats.append(CategoryStats(
            category=cat,
            amount=amount,
            percentage=percentage,
            credit=amounts['credit'],
            debit=amounts['debit']
        ))

    # Sort by total amount (debit + credit)
    category_stats.sort(key=lambda x: x.debit + x.credit, reverse=True)

    return CategoryReport(
        category_stats=category_stats,
        total_amount=total_debit,
        total_credit=total_credit,
        total_debit=total_debit
    )


@router.get("/custom/ranking", response_model=RankingReport)
def get_custom_ranking(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get custom date range ranking report"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    
    expense_ranking = sorted(
        [t for t in transactions if t.transaction_type in ['debit', 'installment']],
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


@router.get("/custom/account", response_model=AccountReport)
def get_custom_account_report(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get custom date range account report"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    
    # Get all user accounts
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    account_map = {acc.id: acc.name for acc in accounts}

    # Calculate account stats
    account_totals = defaultdict(lambda: {'credit': 0.0, 'debit': 0.0})
    for t in transactions:
        if t.transaction_type in ['transfer_out', 'transfer_in']:
            continue
        if t.transaction_type == 'credit':
            account_totals[t.account_id]['credit'] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
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


@router.get("/custom/budget", response_model=BudgetReport)
def get_custom_budget_report(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get custom date range budget report"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get budgets that overlap with the date range
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.start_date < end,
        Budget.end_date >= start
    ).all()
    
    total_budget_amount = sum(b.amount for b in budgets)
    
    budget_categories = set()
    has_global_budget = False
    
    for b in budgets:
        cats = db.query(BudgetCategory.category_name).filter(BudgetCategory.budget_id == b.id).all()
        cat_names = [c[0] for c in cats]
        
        if cat_names:
            budget_categories.update(cat_names)
        elif b.category:
            budget_categories.add(b.category)
        else:
            has_global_budget = True
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    
    budget_transactions = []
    total_spent = 0.0
    
    for t in transactions:
        if t.transaction_type not in ['debit', 'installment']:
            continue
        if t.exclude_from_budget:
            continue
        
        is_included = False
        if has_global_budget:
            is_included = True
        elif t.category in budget_categories:
            is_included = True
        
        if is_included:
            total_spent += t.amount
            budget_transactions.append(BudgetTransaction(
                id=t.id,
                description=t.description,
                amount=t.amount,
                transaction_type=t.transaction_type,
                category=t.category,
                transaction_date=t.transaction_date,
                account_name=t.account_name
            ))
            
    remaining = total_budget_amount - total_spent
    
    # Calculate daily average
    days_diff = (end - start).days + 1
    daily_average = total_spent / days_diff if days_diff > 0 else 0
    
    # Projected spending (simple linear projection)
    # For custom range, we can project based on current progress through the range
    now = datetime.now()
    if start <= now <= end:
        days_passed = (now - start).days + 1
        projected_spending = (total_spent / days_passed) * days_diff if days_passed > 0 else 0
    else:
        projected_spending = total_spent

    status = 'on_track'
    usage_percent = total_spent / total_budget_amount if total_budget_amount > 0 else 0
    
    if total_spent > total_budget_amount:
        status = 'over_budget'
    elif usage_percent > 0.8:
        status = 'warning'
        
    return BudgetReport(
        stats=BudgetStats(
            total_budget=total_budget_amount,
            total_spent=total_spent,
            remaining=remaining,
            daily_average=daily_average,
            projected_spending=projected_spending,
            status=status
        ),
        transactions=budget_transactions
    )


@router.get("/custom/category/{category}/transactions")
def get_custom_category_transactions(
    category: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific category in custom date range"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    filtered = [t for t in transactions if t.category == category]
    
    return filtered


@router.get("/custom/account/{account_id}/transactions")
def get_custom_account_transactions(
    account_id: int,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific account in custom date range"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = get_user_transactions(db, current_user.id, start, end)
    filtered = [t for t in transactions if t.account_id == account_id]
    
    return filtered
