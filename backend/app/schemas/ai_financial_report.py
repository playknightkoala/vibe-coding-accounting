"""
AI財務報告相關的Pydantic schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AIFinancialSummary(BaseModel):
    """AI可讀的財務摘要報告"""

    # 報告元數據
    report_generated_at: datetime
    report_period_start: str
    report_period_end: str
    user_id: int

    # 財務概況
    total_income: float
    total_expense: float
    net_income: float
    savings_rate: float  # 儲蓄率 (淨收入/總收入)

    # 帳戶狀況
    total_assets: float
    accounts_summary: List[dict]  # {name, type, balance, currency}

    # 支出分析
    top_expense_categories: List[dict]  # {category, amount, percentage}
    top_income_categories: List[dict]   # {category, amount, percentage}

    # 預算執行情況
    budgets_summary: List[dict]  # {name, amount, spent, percentage, status}
    total_budget_amount: float
    total_budget_spent: float
    budget_utilization: float  # 預算使用率

    # 交易統計
    total_transactions: int
    average_transaction_amount: float
    largest_expense: Optional[dict]  # {description, amount, date, category}
    largest_income: Optional[dict]   # {description, amount, date, category}

    # 趨勢分析
    daily_average_expense: float
    daily_average_income: float
    expense_trend: str  # "increasing" / "decreasing" / "stable"

    # 警示與建議
    alerts: List[str]  # 超支預算、異常支出等警示
    financial_health_score: float  # 0-100分的財務健康評分

    # 原始文本報告（給AI閱讀）
    text_report: str

    class Config:
        from_attributes = True
