from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class CategoryStats(BaseModel):
    category: str
    amount: float
    percentage: float
    credit: float
    debit: float

class AccountStats(BaseModel):
    account_id: int
    account_name: str
    amount: float
    percentage: float
    credit: float
    debit: float
    balance: float

class TransactionDetail(BaseModel):
    id: int
    description: str
    amount: float
    transaction_type: str
    category: Optional[str]
    transaction_date: datetime
    account_id: int
    account_name: str
    foreign_amount: Optional[float] = None
    foreign_currency: Optional[str] = None

class DailyTransactions(BaseModel):
    date: str
    total_credit: float
    total_debit: float
    transactions: List[TransactionDetail]

class OverviewReport(BaseModel):
    total_credit: float
    total_debit: float
    net_amount: float
    category_stats: List[CategoryStats]
    top_five_income: List[TransactionDetail]
    top_five_expense: List[TransactionDetail]

class DetailsReport(BaseModel):
    daily_transactions: List[DailyTransactions]
    total_credit: float
    total_debit: float

class CategoryReport(BaseModel):
    category_stats: List[CategoryStats]
    total_amount: float
    total_credit: float
    total_debit: float

class RankingReport(BaseModel):
    expense_ranking: List[TransactionDetail]
    income_ranking: List[TransactionDetail]

class AccountReport(BaseModel):
    account_stats: List[AccountStats]
    total_amount: float
