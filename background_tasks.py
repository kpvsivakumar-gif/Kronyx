import schedule
import time
import threading
from datetime import datetime, timedelta
from logger import log, log_error


_scheduler_thread = None
_running = False


def cleanup_old_memories():
    try:
        from database import db
        from config import MEMORY_AUTO_DELETE_DAYS
        cutoff = datetime.utcnow() - timedelta(days=MEMORY_AUTO_DELETE_DAYS)
        cutoff_str = str(cutoff)[:19]
        result = db.table("memories").delete().lt("created_at", cutoff_str).execute()
        log.info(f"CLEANUP old memories before {cutoff_str[:10]}")
    except Exception as e:
        log_error(str(e), context="cleanup_old_memories")


def cleanup_old_cache():
    try:
        from database import db
        cutoff = datetime.utcnow() - timedelta(days=7)
        cutoff_str = str(cutoff)[:19]
        db.table("cache").delete().lt("created_at", cutoff_str).execute()
        log.info(f"CLEANUP old cache entries before {cutoff_str[:10]}")
    except Exception as e:
        log_error(str(e), context="cleanup_old_cache")


def cleanup_old_usage():
    try:
        from database import db
        cutoff = datetime.utcnow() - timedelta(days=90)
        cutoff_str = str(cutoff)[:19]
        db.table("usage").delete().lt("created_at", cutoff_str).execute()
        log.info(f"CLEANUP old usage logs before {cutoff_str[:10]}")
    except Exception as e:
        log_error(str(e), context="cleanup_old_usage")


def cleanup_old_analytics():
    try:
        from database import db
        cutoff = datetime.utcnow() - timedelta(days=180)
        cutoff_str = str(cutoff)[:19]
        db.table("analytics").delete().lt("created_at", cutoff_str).execute()
        log.info(f"CLEANUP old analytics before {cutoff_str[:10]}")
    except Exception as e:
        log_error(str(e), context="cleanup_old_analytics")


def cleanup_old_threats():
    try:
        from database import db
        cutoff = datetime.utcnow() - timedelta(days=30)
        cutoff_str = str(cutoff)[:19]
        db.table("threats").delete().lt("created_at", cutoff_str).execute()
        log.info(f"CLEANUP old threats before {cutoff_str[:10]}")
    except Exception as e:
        log_error(str(e), context="cleanup_old_threats")


def send_rate_limit_warnings():
    try:
        from database import user_get_all, usage_count_today
        from rate_limiter import is_near_limit
        from config import DAILY_API_LIMIT
        users = user_get_all()
        warned = 0
        for user in users[:500]:
            api_key = user.get("api_key_1", "")
            if api_key and is_near_limit(api_key, threshold=0.9):
                used = usage_count_today(api_key)
                from notifications import notify_rate_limit_warning
                notify_rate_limit_warning(api_key, used, DAILY_API_LIMIT)
                warned += 1
        if warned > 0:
            log.info(f"RATE_LIMIT_WARNINGS sent to {warned} users")
    except Exception as e:
        log_error(str(e), context="send_rate_limit_warnings")


def health_monitor():
    try:
        from layers.pulse import health_check
        result = health_check()
        if result.get("status") != "healthy":
            log.warning(f"HEALTH_MONITOR unhealthy: {result}")
        else:
            log.debug(f"HEALTH_MONITOR healthy response_ms={result.get('response_ms', 0)}")
    except Exception as e:
        log_error(str(e), context="health_monitor")


def run_scheduler():
    global _running
    schedule.every().day.at("02:00").do(cleanup_old_memories)
    schedule.every().day.at("02:30").do(cleanup_old_cache)
    schedule.every().day.at("03:00").do(cleanup_old_usage)
    schedule.every().day.at("03:30").do(cleanup_old_analytics)
    schedule.every().day.at("04:00").do(cleanup_old_threats)
    schedule.every().hour.do(send_rate_limit_warnings)
    schedule.every(5).minutes.do(health_monitor)
    log.info("Background scheduler started")
    while _running:
        schedule.run_pending()
        time.sleep(60)
    log.info("Background scheduler stopped")


def start_background_tasks():
    global _scheduler_thread, _running
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _running = True
    _scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    _scheduler_thread.start()
    log.info("Background tasks started")


def stop_background_tasks():
    global _running
    _running = False
    log.info("Background tasks stopping")


def run_task_now(task_name):
    tasks = {
        "cleanup_memories": cleanup_old_memories,
        "cleanup_cache": cleanup_old_cache,
        "cleanup_usage": cleanup_old_usage,
        "cleanup_analytics": cleanup_old_analytics,
        "cleanup_threats": cleanup_old_threats,
        "rate_limit_warnings": send_rate_limit_warnings,
        "health_monitor": health_monitor
    }
    if task_name not in tasks:
        return {"status": "error", "message": f"unknown task. Available: {list(tasks.keys())}"}
    try:
        tasks[task_name]()
        return {"status": "completed", "task": task_name}
    except Exception as e:
        return {"status": "error", "task": task_name, "error": str(e)}


def get_scheduled_tasks():
    return {
        "tasks": [
            {"name": "cleanup_memories", "schedule": "daily at 02:00 UTC"},
            {"name": "cleanup_cache", "schedule": "daily at 02:30 UTC"},
            {"name": "cleanup_usage", "schedule": "daily at 03:00 UTC"},
            {"name": "cleanup_analytics", "schedule": "daily at 03:30 UTC"},
            {"name": "cleanup_threats", "schedule": "daily at 04:00 UTC"},
            {"name": "rate_limit_warnings", "schedule": "every hour"},
            {"name": "health_monitor", "schedule": "every 5 minutes"}
        ],
        "scheduler_running": _running
    }
