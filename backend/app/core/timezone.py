"""
時區處理工具模組
所有時間統一使用台北時間 (Asia/Taipei, UTC+8)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz

# 台北時區
TAIPEI_TZ = pytz.timezone('Asia/Taipei')

def get_taipei_now() -> datetime:
    """獲取當前台北時間 (timezone-aware)"""
    return datetime.now(TAIPEI_TZ)

def to_taipei_time(dt: datetime) -> datetime:
    """
    將任意時區的 datetime 轉換為台北時間
    如果輸入是 naive datetime (無時區資訊)，假設為 UTC
    """
    if dt is None:
        return None

    # 如果是 naive datetime，假設為 UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    # 轉換為台北時間
    return dt.astimezone(TAIPEI_TZ)

def from_iso_string(iso_string: str) -> datetime:
    """
    從 ISO 格式字串解析為 UTC datetime (用於資料庫儲存)
    前端傳來的時間視為台北時間,轉換為 UTC 儲存
    支援格式: "2025-11-26T10:30:00" 或 "2025-11-26T10:30:00Z"
    """
    if not iso_string:
        return None

    # 移除尾部的 Z (UTC 標記) 和毫秒
    cleaned = iso_string.replace('Z', '').split('.')[0]

    # 解析為 naive datetime
    dt = datetime.fromisoformat(cleaned)

    # 假設為台北時間,並轉換為 UTC 儲存
    taipei_dt = TAIPEI_TZ.localize(dt)
    return taipei_dt.astimezone(pytz.utc)

def to_utc(dt: datetime) -> datetime:
    """
    將台北時間轉換為 UTC (用於資料庫儲存)
    """
    if dt is None:
        return None

    # 如果是 naive datetime，假設為台北時間
    if dt.tzinfo is None:
        dt = TAIPEI_TZ.localize(dt)

    # 轉換為 UTC
    return dt.astimezone(pytz.utc)

def format_for_display(dt: datetime) -> str:
    """
    格式化為顯示字串 (台北時間)
    輸出格式: "2025-11-26 18:30:00"
    """
    if dt is None:
        return ""

    taipei_dt = to_taipei_time(dt)
    return taipei_dt.strftime('%Y-%m-%d %H:%M:%S')

def format_for_frontend(dt: datetime) -> str:
    """
    格式化為前端需要的 ISO 格式 (台北時間，不含時區標記)
    輸出格式: "2025-11-26T18:30:00"
    """
    if dt is None:
        return ""

    taipei_dt = to_taipei_time(dt)
    return taipei_dt.strftime('%Y-%m-%dT%H:%M:%S')
