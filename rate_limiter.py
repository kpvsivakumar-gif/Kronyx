from typing import Dict, Tuple
from datetime import datetime, timedelta, date
from database import usage_count_today, usage_count_total, usage_by_layer
from config import (
    DAILY_API_LIMIT_FREE, DAILY_API_LIMIT_PRO,
    DAILY_API_LIMIT_ENTERPRISE, DAILY_API_LIMIT
)
from logger import log_rate_limit, log_warning


# ============================================================
# PLAN LIMITS
# ============================================================

PLAN_LIMITS = {
    "free": DAILY_API_LIMIT_FREE,
    "pro": DAILY_API_LIMIT_PRO,
    "enterprise": DAILY_API_LIMIT_ENTERPRISE
}


def get_limit_for_plan(plan: str) -> int:
    return PLAN_LIMITS.get(plan, DAILY_API_LIMIT_FREE)


# ============================================================
# RATE LIMIT CHECK
# ============================================================

def check_rate_limit(api_key: str, plan: str = "free") -> Dict:
    try:
        limit = get_limit_for_plan(plan)
        used = usage_count_today(api_key)
        remaining = max(0, limit - used)
        allowed = used < limit
        if not allowed:
            log_rate_limit(api_key, used, limit)
        percentage = round((used / limit) * 100, 1) if limit > 0 else 0
        return {
            "allowed": allowed,
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "percentage_used": percentage,
            "plan": plan,
            "message": "Daily limit reached. Resets at midnight UTC." if not allowed else "OK",
            "resets_at": "midnight UTC"
        }
    except Exception as e:
        log_warning(f"Rate limit check failed: {e}")
        return {"allowed": True, "used": 0, "limit": DAILY_API_LIMIT, "remaining": DAILY_API_LIMIT, "percentage_used": 0, "plan": plan, "message": "OK"}


def is_rate_limited(api_key: str, plan: str = "free") -> bool:
    result = check_rate_limit(api_key, plan)
    return not result["allowed"]


def is_near_limit(api_key: str, plan: str = "free", threshold: float = 0.8) -> bool:
    try:
        limit = get_limit_for_plan(plan)
        used = usage_count_today(api_key)
        return (used / limit) >= threshold if limit > 0 else False
    except Exception:
        return False


# ============================================================
# USAGE STATISTICS
# ============================================================

def get_usage_stats(api_key: str, plan: str = "free") -> Dict:
    try:
        limit = get_limit_for_plan(plan)
        used_today = usage_count_today(api_key)
        total_all_time = usage_count_total(api_key)
        by_layer = usage_by_layer(api_key)
        remaining = max(0, limit - used_today)
        percentage = round((used_today / limit) * 100, 1) if limit > 0 else 0
        return {
            "used_today": used_today,
            "limit": limit,
            "remaining": remaining,
            "percentage_used": percentage,
            "total_all_time": total_all_time,
            "plan": plan,
            "by_layer": by_layer[:10],
            "reset_info": get_reset_time()
        }
    except Exception as e:
        log_warning(f"Usage stats failed: {e}")
        return {
            "used_today": 0, "limit": DAILY_API_LIMIT, "remaining": DAILY_API_LIMIT,
            "percentage_used": 0, "total_all_time": 0, "plan": plan, "by_layer": []
        }


# ============================================================
# RESET TIME
# ============================================================

def get_reset_time() -> Dict:
    try:
        now = datetime.utcnow()
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        seconds_until_reset = int((tomorrow - now).total_seconds())
        hours = seconds_until_reset // 3600
        minutes = (seconds_until_reset % 3600) // 60
        return {
            "resets_at": "midnight UTC",
            "resets_at_iso": tomorrow.isoformat() + "Z",
            "seconds_until_reset": seconds_until_reset,
            "minutes_until_reset": seconds_until_reset // 60,
            "hours_until_reset": hours,
            "human_readable": f"{hours}h {minutes}m until reset"
        }
    except Exception:
        return {"resets_at": "midnight UTC", "seconds_until_reset": 86400}


# ============================================================
# BURST RATE LIMITING
# ============================================================

_burst_tracker: Dict[str, Dict] = {}


def check_burst_limit(api_key: str, max_per_second: int = 10) -> bool:
    try:
        now = datetime.utcnow()
        if api_key not in _burst_tracker:
            _burst_tracker[api_key] = {"count": 1, "window_start": now}
            return True
        data = _burst_tracker[api_key]
        window_end = data["window_start"] + timedelta(seconds=1)
        if now > window_end:
            _burst_tracker[api_key] = {"count": 1, "window_start": now}
            return True
        data["count"] += 1
        if data["count"] > max_per_second:
            log_warning(f"Burst limit exceeded", api_key=api_key)
            return False
        return True
    except Exception:
        return True


# ============================================================
# USAGE ALERTS
# ============================================================

def check_usage_alert(api_key: str, plan: str = "free") -> Dict:
    try:
        stats = get_usage_stats(api_key, plan)
        percentage = stats.get("percentage_used", 0)
        alerts = []
        if percentage >= 100:
            alerts.append({"level": "critical", "message": "Daily limit reached. Upgrade plan for more usage."})
        elif percentage >= 90:
            alerts.append({"level": "warning", "message": f"Usage at {percentage}% of daily limit."})
        elif percentage >= 75:
            alerts.append({"level": "info", "message": f"Usage at {percentage}% of daily limit."})
        return {
            "has_alert": len(alerts) > 0,
            "alerts": alerts,
            "usage_percentage": percentage
        }
    except Exception:
        return {"has_alert": False, "alerts": [], "usage_percentage": 0}
