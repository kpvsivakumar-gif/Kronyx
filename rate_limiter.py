from database import usage_count_today, usage_count_total
from config import DAILY_API_LIMIT
from logger import log_security


def check_rate_limit(api_key):
    used = usage_count_today(api_key)
    remaining = max(0, DAILY_API_LIMIT - used)
    allowed = used < DAILY_API_LIMIT
    if not allowed:
        log_security("rate_limit_hit", api_key=api_key)
    return {"allowed": allowed, "used": used, "limit": DAILY_API_LIMIT, "remaining": remaining}


def get_usage_stats(api_key):
    used = usage_count_today(api_key)
    total = usage_count_total(api_key)
    return {"used_today": used, "limit": DAILY_API_LIMIT, "remaining": max(0, DAILY_API_LIMIT - used), "percentage_used": round((used / DAILY_API_LIMIT) * 100, 1), "total_all_time": total}


def is_near_limit(api_key, threshold=0.8):
    used = usage_count_today(api_key)
    return (used / DAILY_API_LIMIT) >= threshold


def get_reset_time():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_until_reset = int((tomorrow - now).total_seconds())
    return {"resets_at": "midnight UTC", "seconds_until_reset": seconds_until_reset, "minutes_until_reset": seconds_until_reset // 60}
