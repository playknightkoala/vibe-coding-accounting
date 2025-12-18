from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date, timezone
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
from app.schemas.ai_financial_report import AIFinancialSummary
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
    
    # Process budgets to pre-load constraints
    processed_budgets = []
    for b in budgets:
        # Fetch categories
        cats = db.query(BudgetCategory.category_name).filter(BudgetCategory.budget_id == b.id).all()
        categories = {c[0] for c in cats}
        if b.category:
            categories.add(b.category)
            
        # Fetch accounts (lazy load, but strictly for filtering)
        # Note: If no accounts linked, it means all accounts
        linked_accounts = {acc.id for acc in b.accounts} if b.accounts else set()
        
        processed_budgets.append({
            "budget": b,
            "categories": categories,
            "accounts": linked_accounts,
            "has_categories": bool(categories),
            "start": b.start_date,
            "end": b.end_date
        })

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
            
        # Check if transaction matches ANY budget
        is_included = False
        
        for pb in processed_budgets:
            # 1. Date Check (Strictly for the budget's range)
            # Transaction query already filters by report range, but budget might be shorter?
            # Usually budget covers the month context in get_monthly_budget_report, but let's be safe
            # Use date() comparison to avoid timezone issues (fixed previously)
            if t.transaction_date.date() < pb["start"].date() or t.transaction_date.date() > pb["end"].date():
                continue

            # 2. Account Check
            if pb["accounts"] and t.account_id not in pb["accounts"]:
                continue
                
            # 3. Category Check
            if pb["has_categories"]:
                if t.category not in pb["categories"]:
                    continue
            # If has_categories is False, it's a global budget (matches all categories)
            
            # If we passed all checks, this transaction is included
            is_included = True
            break
            
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
    
    # Process budgets to pre-load constraints
    processed_budgets = []
    for b in budgets:
        # Fetch categories
        cats = db.query(BudgetCategory.category_name).filter(BudgetCategory.budget_id == b.id).all()
        categories = {c[0] for c in cats}
        if b.category:
            categories.add(b.category)
            
        # Fetch accounts
        linked_accounts = {acc.id for acc in b.accounts} if b.accounts else set()
        
        processed_budgets.append({
            "budget": b,
            "categories": categories,
            "accounts": linked_accounts,
            "has_categories": bool(categories),
            "start": b.start_date,
            "end": b.end_date
        })

    transactions = get_user_transactions(db, current_user.id, start_date, end_date)
    
    budget_transactions = []
    total_spent = 0.0
    
    for t in transactions:
        if t.transaction_type not in ['debit', 'installment']:
            continue
            
        if t.exclude_from_budget:
            continue
            
        # Check if transaction matches ANY budget
        is_included = False
        
        for pb in processed_budgets:
            # 1. Date Check
            if t.transaction_date.date() < pb["start"].date() or t.transaction_date.date() > pb["end"].date():
                continue

            # 2. Account Check
            if pb["accounts"] and t.account_id not in pb["accounts"]:
                continue
                
            # 3. Category Check
            if pb["has_categories"]:
                if t.category not in pb["categories"]:
                    continue
            
            is_included = True
            break
            
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
    
    processed_budgets = []
    for b in budgets:
        # Fetch categories
        cats = db.query(BudgetCategory.category_name).filter(BudgetCategory.budget_id == b.id).all()
        categories = {c[0] for c in cats}
        if b.category:
            categories.add(b.category)
            
        # Fetch accounts
        linked_accounts = {acc.id for acc in b.accounts} if b.accounts else set()
        
        processed_budgets.append({
            "budget": b,
            "categories": categories,
            "accounts": linked_accounts,
            "has_categories": bool(categories),
            "start": b.start_date,
            "end": b.end_date
        })

    transactions = get_user_transactions(db, current_user.id, start, end)
    
    budget_transactions = []
    total_spent = 0.0
    
    for t in transactions:
        if t.transaction_type not in ['debit', 'installment']:
            continue
        if t.exclude_from_budget:
            continue
            
        # Check if transaction matches ANY budget
        is_included = False
        
        for pb in processed_budgets:
            # 1. Date Check
            if t.transaction_date.date() < pb["start"].date() or t.transaction_date.date() > pb["end"].date():
                continue

            # 2. Account Check
            if pb["accounts"] and t.account_id not in pb["accounts"]:
                continue
                
            # 3. Category Check
            if pb["has_categories"]:
                if t.category not in pb["categories"]:
                    continue
            
            is_included = True
            break
         
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
    now = datetime.now(timezone.utc)
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


@router.get("/ai-financial-summary", response_model=AIFinancialSummary)
def get_ai_financial_summary(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成AI可讀的綜合財務報告
    整合所有財務數據，包括收支概況、帳戶狀況、預算執行、趨勢分析等
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        end = datetime.combine(end.date(), datetime.max.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    now = datetime.now(timezone.utc)

    # 1. 獲取所有交易
    transactions = get_user_transactions(db, current_user.id, start, end)

    # 2. 獲取所有帳戶及餘額
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    total_assets = sum(acc.balance for acc in accounts)
    accounts_summary = [
        {
            "name": acc.name,
            "type": acc.account_type,
            "balance": acc.balance,
            "currency": acc.currency
        }
        for acc in accounts
    ]

    # 3. 計算收入與支出
    total_income = 0.0
    total_expense = 0.0
    category_income = defaultdict(float)
    category_expense = defaultdict(float)

    for t in transactions:
        if t.transaction_type == 'credit':
            total_income += t.amount
            category = t.category or "未分類"
            category_income[category] += t.amount
        elif t.transaction_type in ['debit', 'installment']:
            if not t.exclude_from_budget:
                total_expense += t.amount
                category = t.category or "未分類"
                category_expense[category] += t.amount

    net_income = total_income - total_expense
    savings_rate = (net_income / total_income * 100) if total_income > 0 else 0.0

    # 4. 支出類別排名 (top 5)
    top_expense_categories = [
        {
            "category": cat,
            "amount": amt,
            "percentage": round(amt / total_expense * 100, 2) if total_expense > 0 else 0.0
        }
        for cat, amt in sorted(category_expense.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # 5. 收入類別排名 (top 5)
    top_income_categories = [
        {
            "category": cat,
            "amount": amt,
            "percentage": round(amt / total_income * 100, 2) if total_income > 0 else 0.0
        }
        for cat, amt in sorted(category_income.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # 6. 獲取預算執行情況
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.start_date < end,
        Budget.end_date >= start
    ).all()

    total_budget_amount = sum(b.amount for b in budgets)
    total_budget_spent = 0.0
    budgets_summary = []

    for budget in budgets:
        # 計算此預算的實際支出
        budget_categories = set()
        has_global_budget = False

        cats = db.query(BudgetCategory.category_name).filter(
            BudgetCategory.budget_id == budget.id
        ).all()
        cat_names = [c[0] for c in cats]

        if cat_names:
            budget_categories.update(cat_names)
        elif budget.category:
            budget_categories.add(budget.category)
        else:
            has_global_budget = True

        spent = 0.0
        for t in transactions:
            if t.transaction_type not in ['debit', 'installment']:
                continue
            if t.exclude_from_budget:
                continue

            # 只計算預算時間段內的交易
            if t.transaction_date.date() < budget.start_date.date() or t.transaction_date.date() > budget.end_date.date():
                continue

            # 檢查是否為綁定帳戶的交易
            # 若預算有綁定帳戶，且此交易不屬於這些帳戶，則排除
            if budget.accounts:
                linked_account_ids = {acc.id for acc in budget.accounts}
                if t.account_id not in linked_account_ids:
                    continue

            is_included = False
            if has_global_budget:
                is_included = True
            elif t.category in budget_categories:
                is_included = True

            if is_included:
                spent += t.amount

        total_budget_spent += spent
        percentage = round(spent / budget.amount * 100, 2) if budget.amount > 0 else 0.0

        status = "正常"
        if spent > budget.amount:
            status = "超支"
        elif percentage >= 80:
            status = "警告"

        budgets_summary.append({
            "name": budget.name,
            "amount": budget.amount,
            "spent": spent,
            "percentage": percentage,
            "status": status,
            "start_date": budget.start_date.strftime('%Y-%m-%d'),
            "end_date": budget.end_date.strftime('%Y-%m-%d'),
            "period": f"{budget.start_date.strftime('%Y-%m-%d')} ~ {budget.end_date.strftime('%Y-%m-%d')}"
        })

    budget_utilization = (total_budget_spent / total_budget_amount * 100) if total_budget_amount > 0 else 0.0

    # 7. 交易統計
    total_transactions = len(transactions)
    average_transaction_amount = (total_income + total_expense) / total_transactions if total_transactions > 0 else 0.0

    # 找出最大支出和收入
    expense_transactions = [t for t in transactions if t.transaction_type in ['debit', 'installment']]
    income_transactions = [t for t in transactions if t.transaction_type == 'credit']

    largest_expense = None
    if expense_transactions:
        largest_exp = max(expense_transactions, key=lambda x: x.amount)
        largest_expense = {
            "description": largest_exp.description,
            "amount": largest_exp.amount,
            "date": largest_exp.transaction_date.strftime('%Y-%m-%d'),
            "category": largest_exp.category or "未分類"
        }

    largest_income = None
    if income_transactions:
        largest_inc = max(income_transactions, key=lambda x: x.amount)
        largest_income = {
            "description": largest_inc.description,
            "amount": largest_inc.amount,
            "date": largest_inc.transaction_date.strftime('%Y-%m-%d'),
            "category": largest_inc.category or "未分類"
        }

    # 8. 趨勢分析
    days_in_period = (end.date() - start.date()).days + 1
    daily_average_expense = total_expense / days_in_period if days_in_period > 0 else 0.0
    daily_average_income = total_income / days_in_period if days_in_period > 0 else 0.0

    # 簡單的趨勢分析：比較前半段和後半段
    # 使用日期比較避免時區問題
    mid_date = start.date() + (end.date() - start.date()) // 2
    first_half_expense = sum(t.amount for t in transactions
                             if t.transaction_type in ['debit', 'installment']
                             and t.transaction_date.date() < mid_date)
    second_half_expense = sum(t.amount for t in transactions
                              if t.transaction_type in ['debit', 'installment']
                              and t.transaction_date.date() >= mid_date)

    if second_half_expense > first_half_expense * 1.1:
        expense_trend = "遞增"
    elif second_half_expense < first_half_expense * 0.9:
        expense_trend = "遞減"
    else:
        expense_trend = "穩定"

    # 9. 警示與建議
    alerts = []
    for budget in budgets_summary:
        if budget["status"] == "超支":
            alerts.append(f"預算「{budget['name']}」已超支 {budget['percentage'] - 100:.1f}%")
        elif budget["status"] == "警告":
            alerts.append(f"預算「{budget['name']}」使用率達 {budget['percentage']:.1f}%，接近上限")

    # 檢查異常大額支出（超過平均支出的3倍）
    if expense_transactions:
        avg_expense = sum(t.amount for t in expense_transactions) / len(expense_transactions)
        abnormal_expenses = [t for t in expense_transactions if t.amount > avg_expense * 3]
        if abnormal_expenses:
            alerts.append(f"發現 {len(abnormal_expenses)} 筆異常大額支出（超過平均值3倍）")

    # 檢查儲蓄率
    if savings_rate < 0:
        alerts.append(f"本期支出大於收入，淨收入為負（{net_income:.2f}）")
    elif savings_rate < 10:
        alerts.append(f"儲蓄率偏低（{savings_rate:.1f}%），建議控制支出")

    # 10. 財務健康評分 (0-100)
    health_score = 100.0

    # 儲蓄率評分 (最多40分)
    if savings_rate < 0:
        health_score -= 40
    elif savings_rate < 10:
        health_score -= 30
    elif savings_rate < 20:
        health_score -= 20
    elif savings_rate < 30:
        health_score -= 10

    # 預算執行評分 (最多30分)
    over_budget_count = sum(1 for b in budgets_summary if b["status"] == "超支")
    if over_budget_count > 0:
        health_score -= min(30, over_budget_count * 15)

    # 支出趨勢評分 (最多15分)
    if expense_trend == "遞增":
        health_score -= 15
    elif expense_trend == "穩定":
        health_score -= 5

    # 異常支出評分 (最多15分)
    if expense_transactions:
        avg_expense = sum(t.amount for t in expense_transactions) / len(expense_transactions)
        abnormal_count = sum(1 for t in expense_transactions if t.amount > avg_expense * 3)
        if abnormal_count > 0:
            health_score -= min(15, abnormal_count * 5)

    health_score = max(0, health_score)

    # 11. 生成文本報告 (Prompt格式)
    text_report = f"""
你是一位專業的財務顧問，請根據以下財務數據提供詳細的分析與建議。

=== 財務數據報告 ===
報告期間: {start_date} 至 {end_date}
數據生成時間: {now.strftime('%Y-%m-%d %H:%M:%S')}

【財務概況】
總收入: ${total_income:,.2f}
總支出: ${total_expense:,.2f}
淨收入: ${net_income:,.2f}
儲蓄率: {savings_rate:.1f}%

【資產狀況】
總資產: ${total_assets:,.2f}
帳戶數量: {len(accounts)}

帳戶明細:
"""

    for acc in accounts_summary:
        text_report += f"  - {acc['name']} ({acc['type']}): {acc['currency']} ${acc['balance']:,.2f}\n"

    text_report += f"""
【支出分析】
前五大支出類別:
"""
    for i, cat in enumerate(top_expense_categories, 1):
        text_report += f"  {i}. {cat['category']}: ${cat['amount']:,.2f} ({cat['percentage']:.1f}%)\n"

    text_report += f"""
【收入分析】
前五大收入類別:
"""
    for i, cat in enumerate(top_income_categories, 1):
        text_report += f"  {i}. {cat['category']}: ${cat['amount']:,.2f} ({cat['percentage']:.1f}%)\n"

    text_report += f"""
【預算執行】
總預算金額: ${total_budget_amount:,.2f}
已使用金額: ${total_budget_spent:,.2f}
預算使用率: {budget_utilization:.1f}%

預算明細:
"""
    for budget in budgets_summary:
        text_report += f"  - {budget['name']}: ${budget['spent']:,.2f} / ${budget['amount']:,.2f} ({budget['percentage']:.1f}%) [{budget['status']}] ({budget['start_date']} ~ {budget['end_date']})\n"

    text_report += f"""
【交易統計】
交易總數: {total_transactions}
平均交易金額: ${average_transaction_amount:,.2f}
每日平均支出: ${daily_average_expense:,.2f}
每日平均收入: ${daily_average_income:,.2f}
支出趨勢: {expense_trend}

最大單筆支出: {largest_expense['description'] if largest_expense else '無'} - ${largest_expense['amount']:,.2f} ({largest_expense['date']}) [{largest_expense['category']}]
最大單筆收入: {largest_income['description'] if largest_income else '無'} - ${largest_income['amount']:,.2f} ({largest_income['date']}) [{largest_income['category']}]

【財務健康評分】
{health_score:.1f} / 100 分

評分說明:
- 90-100分: 財務狀況優秀
- 70-89分: 財務狀況良好
- 50-69分: 財務狀況一般，需要注意
- 0-49分: 財務狀況較差，需要改善

【警示與建議】
"""

    if alerts:
        for alert in alerts:
            text_report += f"[!] {alert}\n"
    else:
        text_report += "[OK] 目前沒有需要特別注意的財務警示\n"

    text_report += """
=== 分析要求 ===

請基於以上完整的財務數據，提供專業的財務分析報告，包含以下內容：

1. 【支出結構分析】
   - 分析支出分佈是否合理
   - 指出可能存在的過度支出領域
   - 提供具體的優化建議

2. 【預算執行評估】
   - 評估預算使用情況
   - 分析預算分配是否合理
   - 建議如何調整預算策略

3. 【收入狀況分析】
   - 評估收入來源的穩定性
   - 分析收入結構的健康度
   - 提供增加收入的建議

4. 【儲蓄能力評估】
   - 評估當前儲蓄率是否健康
   - 分析影響儲蓄的主要因素
   - 提供提高儲蓄率的具體方法

5. 【財務趨勢預測】
   - 根據當前趨勢預測未來財務狀況
   - 指出可能的財務風險
   - 提供預防措施

6. 【具體改善建議】
   - 提供至少5條可執行的財務改善建議
   - 每條建議需包含具體執行步驟
   - 標明建議的優先級

請以專業、易懂的方式呈現分析結果，並提供可操作的建議。
"""

    return AIFinancialSummary(
        report_generated_at=now,
        report_period_start=start_date,
        report_period_end=end_date,
        user_id=current_user.id,
        total_income=total_income,
        total_expense=total_expense,
        net_income=net_income,
        savings_rate=savings_rate,
        total_assets=total_assets,
        accounts_summary=accounts_summary,
        top_expense_categories=top_expense_categories,
        top_income_categories=top_income_categories,
        budgets_summary=budgets_summary,
        total_budget_amount=total_budget_amount,
        total_budget_spent=total_budget_spent,
        budget_utilization=budget_utilization,
        total_transactions=total_transactions,
        average_transaction_amount=average_transaction_amount,
        largest_expense=largest_expense,
        largest_income=largest_income,
        daily_average_expense=daily_average_expense,
        daily_average_income=daily_average_income,
        expense_trend=expense_trend,
        alerts=alerts,
        financial_health_score=health_score,
        text_report=text_report
    )
