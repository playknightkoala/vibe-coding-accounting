"""
預算週期計算輔助函數
"""
from datetime import datetime, timedelta
from typing import Tuple
import calendar


def calculate_period_range(period_type: str, reference_date: datetime = None) -> Tuple[datetime, datetime]:
    """
    根據週期類型計算開始和結束時間

    Args:
        period_type: 'monthly', 'quarterly', 'yearly'
        reference_date: 參考日期，默認為當前時間

    Returns:
        (start_datetime, end_datetime) 元組
    """
    if reference_date is None:
        reference_date = datetime.now()

    if period_type == 'monthly':
        return _calculate_monthly_range(reference_date)
    elif period_type == 'quarterly':
        return _calculate_quarterly_range(reference_date)
    elif period_type == 'yearly':
        return _calculate_yearly_range(reference_date)
    else:
        raise ValueError(f"Invalid period_type: {period_type}")


def _calculate_monthly_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    計算每月週期範圍
    起始: 當月1日 00:00
    結束: 當月最後一天 23:59
    """
    year = ref_date.year
    month = ref_date.month

    # 開始時間: 當月1日 00:00
    start_date = datetime(year, month, 1, 0, 0)

    # 結束時間: 當月最後一天 23:59
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59)

    return (start_date, end_date)


def _calculate_quarterly_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    計算每季週期範圍
    Q1: 01/01 ~ 03/31
    Q2: 04/01 ~ 06/30
    Q3: 07/01 ~ 09/30
    Q4: 10/01 ~ 12/31
    """
    year = ref_date.year
    month = ref_date.month

    # 判斷當前是第幾季
    if month <= 3:
        quarter = 1
        start_month = 1
        end_month = 3
    elif month <= 6:
        quarter = 2
        start_month = 4
        end_month = 6
    elif month <= 9:
        quarter = 3
        start_month = 7
        end_month = 9
    else:
        quarter = 4
        start_month = 10
        end_month = 12

    # 開始時間: 季度第一個月的第1日 00:00
    start_date = datetime(year, start_month, 1, 0, 0)

    # 結束時間: 季度最後一個月的最後一天 23:59
    last_day = calendar.monthrange(year, end_month)[1]
    end_date = datetime(year, end_month, last_day, 23, 59)

    return (start_date, end_date)


def _calculate_yearly_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    計算每年週期範圍
    起始: 01/01 00:00
    結束: 12/31 23:59
    """
    year = ref_date.year

    # 開始時間: 1月1日 00:00
    start_date = datetime(year, 1, 1, 0, 0)

    # 結束時間: 12月31日 23:59
    end_date = datetime(year, 12, 31, 23, 59)

    return (start_date, end_date)


def calculate_next_period_range(period_type: str, current_end_date: datetime) -> Tuple[datetime, datetime]:
    """
    計算下一個週期的時間範圍

    Args:
        period_type: 'monthly', 'quarterly', 'yearly'
        current_end_date: 當前週期的結束時間

    Returns:
        (next_start_datetime, next_end_datetime) 元組
    """
    # 下一個週期的起始時間 = 當前結束時間 + 1分鐘
    next_period_start = current_end_date + timedelta(minutes=1)

    # 根據週期類型計算下一個週期的範圍
    return calculate_period_range(period_type, next_period_start)
