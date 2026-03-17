import os
from database import (
    admin_get_global_stats, admin_get_user_breakdown,
    user_get_all, user_count, user_delete,
    memory_count_active, usage_count_total, threat_count_total
)
from logger import log, log_security


def verify_admin_key(key):
    admin_key = os.getenv("ADMIN_KEY", "")
    if not admin_key:
        return False
    return key == admin_key


def get_global_stats():
    stats = admin_get_global_stats()
    stats["total_registered_users"] = user_count()
    return stats


def get_all_users():
    users = user_get_all()
    safe_users = []
    for user in users:
        safe_users.append({
            "id": user.get("id", ""),
            "email": user.get("email", "")[:40],
            "key_1_preview": user.get("api_key_1", "")[:12] + "****",
            "key_2_preview": user.get("api_key_2", "")[:12] + "****",
            "joined": str(user.get("created_at", ""))[:10]
        })
    return {"users": safe_users, "total": len(safe_users)}


def get_user_breakdown():
    breakdown = admin_get_user_breakdown()
    return {"breakdown": breakdown, "total": len(breakdown)}


def get_top_users_by_usage(limit=20):
    users = user_get_all()
    user_stats = []
    for user in users[:200]:
        api_key = user.get("api_key_1", "")
        if api_key:
            total = usage_count_total(api_key)
            if total > 0:
                user_stats.append({
                    "email": user.get("email", "")[:40],
                    "total_api_calls": total,
                    "active_memories": memory_count_active(api_key),
                    "threats_blocked": threat_count_total(api_key)
                })
    user_stats.sort(key=lambda x: x["total_api_calls"], reverse=True)
    return {"top_users": user_stats[:limit], "total_active_users": len(user_stats)}


def get_system_health():
    from layers.pulse import health_check
    health = health_check()
    from background_tasks import get_scheduled_tasks
    tasks = get_scheduled_tasks()
    return {
        "system_health": health,
        "background_tasks": tasks,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0"
    }


def delete_user_account(user_id, admin_key):
    if not verify_admin_key(admin_key):
        return {"status": "error", "message": "invalid admin key"}
    log_security("admin_delete_user", detail=f"user_id={user_id[:20]}")
    success = user_delete(user_id)
    if not success:
        return {"status": "error", "message": "user not found or delete failed"}
    return {"status": "deleted", "user_id": user_id}


def run_maintenance_task(task_name, admin_key):
    if not verify_admin_key(admin_key):
        return {"status": "error", "message": "invalid admin key"}
    from background_tasks import run_task_now
    log.info(f"ADMIN running task: {task_name}")
    return run_task_now(task_name)


def get_usage_overview():
    from database import db
    try:
        from datetime import date
        today = str(date.today())
        today_usage = db.table("usage").select("id", count="exact").gte("created_at", today).execute()
        total_usage = db.table("usage").select("id", count="exact").execute()
        total_threats = db.table("threats").select("id", count="exact").execute()
        today_signups = db.table("users").select("id", count="exact").gte("created_at", today).execute()
        return {
            "today": {
                "api_calls": today_usage.count or 0,
                "new_signups": today_signups.count or 0
            },
            "all_time": {
                "total_api_calls": total_usage.count or 0,
                "total_threats_blocked": total_threats.count or 0,
                "total_users": user_count()
            }
        }
    except Exception:
        return {"error": "could not fetch overview"}


def get_layer_usage_overview():
    from database import db
    try:
        result = db.table("usage").select("layer").limit(10000).execute()
        layer_counts = {}
        for row in (result.data or []):
            l = row.get("layer", "unknown")
            layer_counts[l] = layer_counts.get(l, 0) + 1
        sorted_layers = sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)
        return {
            "layer_usage": [{"layer": k, "total_calls": v} for k, v in sorted_layers],
            "most_popular_layer": sorted_layers[0][0] if sorted_layers else "none"
        }
    except Exception:
        return {"layer_usage": []}
