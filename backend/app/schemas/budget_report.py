from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BudgetTransaction(BaseModel):
    id: int
    description: str
    amount: float
    transaction_type: str
    category: Optional[str]
    transaction_date: datetime
    account_name: str

class BudgetStats(BaseModel):
    total_budget: float
    total_spent: float
    remaining: float
    daily_average: float
    projected_spending: float
    status: str  # 'under_budget', 'over_budget', 'on_track'

class BudgetReport(BaseModel):
    stats: BudgetStats
    transactions: List[BudgetTransaction]
