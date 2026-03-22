from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import os
from logger import log_error, log_database_event

# ============================================================
# DATABASE CONNECTION
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

db: Optional[Client] = None

def _connect():
    global db
    try:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if url and key:
            db = create_client(url, key)
            log_database_event("connection", "Supabase connected", success=True)
        else:
            log_error("SUPABASE_URL or SUPABASE_KEY missing", context="database_startup")
    except Exception as e:
        log_error(f"Database connection failed: {e}", context="database_startup")
        db = None

_connect()


def get_db() -> Optional[Client]:
    return db


def is_db_connected() -> bool:
    return db is not None


def _db():
    if db is None:
        _connect()
    return db


# ============================================================
# USER OPERATIONS
# ============================================================

def user_create(email: str, password_hash: str, key1: str, key2: str) -> Dict:
    try:
        result = db.table("users").insert({
            "email": email.lower().strip(),
            "password": password_hash,
            "api_key_1": key1,
            "api_key_2": key2
        }).execute()
        if result.data:
            log_database_event("user_create", f"email={email[:20]}", success=True)
            return result.data[0]
        return {"error": "no data returned"}
    except Exception as e:
        log_error(str(e), context="user_create")
        return {"error": str(e)}


def user_get_by_email(email: str) -> Optional[Dict]:
    try:
        if not email:
            return None
        result = db.table("users").select("*").eq("email", email.lower().strip()).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        log_error(str(e), context="user_get_by_email")
        return None


def user_get_by_key(api_key: str) -> Optional[Dict]:
    try:
        if not api_key:
            return None
        r1 = db.table("users").select("*").eq("api_key_1", api_key).execute()
        if r1.data:
            return r1.data[0]
        r2 = db.table("users").select("*").eq("api_key_2", api_key).execute()
        return r2.data[0] if r2.data else None
    except Exception as e:
        log_error(str(e), context="user_get_by_key")
        return None


def user_get_by_id(user_id: str) -> Optional[Dict]:
    try:
        result = db.table("users").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        log_error(str(e), context="user_get_by_id")
        return None


def user_update_key(user_id: str, key_number: int, new_key: str) -> bool:
    try:
        _db().table("users").update({
            f"api_key_{key_number}": new_key,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        log_database_event("user_update_key", f"key_number={key_number}", success=True)
        return True
    except Exception as e:
        log_error(str(e), context="user_update_key")
        return False


def user_update_password(user_id: str, new_hash: str) -> bool:
    try:
        _db().table("users").update({
            "password": new_hash,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_update_password")
        return False


def user_update_plan(user_id: str, plan: str) -> bool:
    try:
        valid_plans = ["free", "pro", "enterprise"]
        if plan not in valid_plans:
            return False
        _db().table("users").update({
            "plan": plan,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_update_plan")
        return False


def user_deactivate(user_id: str) -> bool:
    try:
        _db().table("users").update({
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_deactivate")
        return False


def user_delete(user_id: str) -> bool:
    try:
        _db().table("users").delete().eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_delete")
        return False


def user_get_all(limit: int = 1000) -> List[Dict]:
    try:
        result = db.table("users").select(
            "id, email, api_key_1, api_key_2, plan, is_active, created_at"
        ).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        log_error(str(e), context="user_get_all")
        return []


def user_count() -> int:
    try:
        result = db.table("users").select("id", count="exact").execute()
        return result.count or 0
    except Exception:
        return 0


def user_count_active() -> int:
    try:
        result = db.table("users").select("id", count="exact").eq("is_active", True).execute()
        return result.count or 0
    except Exception:
        return 0


def user_count_by_plan(plan: str) -> int:
    try:
        result = db.table("users").select("id", count="exact").eq("plan", plan).execute()
        return result.count or 0
    except Exception:
        return 0


def user_exists(email: str) -> bool:
    try:
        result = db.table("users").select("id").eq("email", email.lower().strip()).execute()
        return len(result.data or []) > 0
    except Exception:
        return False


# ============================================================
# USAGE TRACKING
# ============================================================

def usage_log(api_key: str, layer: str, endpoint: str) -> None:
    try:
        _db().table("nexus_usage").insert({
            "api_key": api_key,
            "layer": layer,
            "endpoint": endpoint
        }).execute()
    except Exception as e:
        log_error(str(e), context="usage_log")


def usage_count_today(api_key: str) -> int:
    try:
        today = str(date.today())
        result = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).gte("created_at", today).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_count_total(api_key: str) -> int:
    try:
        result = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_count_by_layer(api_key: str, layer: str) -> int:
    try:
        result = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).eq("layer", layer).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_by_layer(api_key: str) -> List[Dict]:
    try:
        result = db.table("nexus_usage").select("layer").eq("api_key", api_key).execute()
        layer_counts: Dict[str, int] = {}
        for row in (result.data or []):
            l = row.get("layer", "unknown")
            layer_counts[l] = layer_counts.get(l, 0) + 1
        return sorted(
            [{"layer": k, "count": v} for k, v in layer_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )
    except Exception:
        return []


def usage_by_date_range(api_key: str, start_date: str, end_date: str) -> int:
    try:
        result = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).gte("created_at", start_date).lte("created_at", end_date).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_get_recent(api_key: str, limit: int = 100) -> List[Dict]:
    try:
        result = db.table("nexus_usage").select("layer, endpoint, created_at").eq("api_key", api_key).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception:
        return []


# ============================================================
# ADMIN STATISTICS
# ============================================================

def admin_get_global_stats() -> Dict:
    try:
        users_total = db.table("users").select("id", count="exact").execute()
        users_active = db.table("users").select("id", count="exact").eq("is_active", True).execute()
        memories = db.table("memories").select("id", count="exact").execute()
        usage = db.table("nexus_usage").select("id", count="exact").execute()
        threats = db.table("aegis_threats").select("id", count="exact").execute()
        today = str(date.today())
        today_signups = db.table("users").select("id", count="exact").gte("created_at", today).execute()
        today_usage = db.table("nexus_usage").select("id", count="exact").gte("created_at", today).execute()
        today_threats = db.table("aegis_threats").select("id", count="exact").gte("created_at", today).execute()
        return {
            "total_users": users_total.count or 0,
            "active_users": users_active.count or 0,
            "total_memories": memories.count or 0,
            "total_api_calls": usage.count or 0,
            "total_threats_blocked": threats.count or 0,
            "new_users_today": today_signups.count or 0,
            "api_calls_today": today_usage.count or 0,
            "threats_today": today_threats.count or 0
        }
    except Exception as e:
        log_error(str(e), context="admin_get_global_stats")
        return {
            "total_users": 0, "active_users": 0, "total_memories": 0,
            "total_api_calls": 0, "total_threats_blocked": 0,
            "new_users_today": 0, "api_calls_today": 0, "threats_today": 0
        }


# ============================================================
# EVOLVE TRACKING
# ============================================================

def evolve_log(api_key: str, question: str, response: str, score: int, layer: str = "") -> None:
    try:
        _db().table("evolve_data").insert({
            "api_key": api_key,
            "question": question[:300],
            "response": response[:600],
            "score": max(0, min(100, int(score))),
            "layer": layer[:50]
        }).execute()
    except Exception as e:
        log_error(str(e), context="evolve_log")


def evolve_get_performance(api_key: str) -> Dict:
    try:
        result = db.table("evolve_data").select("score, created_at").eq("api_key", api_key).order("created_at", desc=True).limit(100).execute()
        if not result.data:
            return {"average_score": 0, "total_tracked": 0, "trend": "no_data", "min_score": 0, "max_score": 0}
        scores = [r["score"] for r in result.data if r.get("score") is not None]
        if not scores:
            return {"average_score": 0, "total_tracked": 0, "trend": "no_data", "min_score": 0, "max_score": 0}
        avg = round(sum(scores) / len(scores), 1)
        recent = scores[:10]
        older = scores[10:20] if len(scores) > 10 else scores
        trend = "stable"
        if older and recent:
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            if recent_avg > older_avg + 3:
                trend = "improving"
            elif recent_avg < older_avg - 3:
                trend = "declining"
        return {
            "average_score": avg,
            "total_tracked": len(scores),
            "trend": trend,
            "min_score": min(scores),
            "max_score": max(scores),
            "recent_10_avg": round(sum(recent) / len(recent), 1) if recent else 0
        }
    except Exception as e:
        log_error(str(e), context="evolve_get_performance")
        return {"average_score": 0, "total_tracked": 0, "trend": "error", "min_score": 0, "max_score": 0}


# ============================================================
# NOTIFICATIONS
# ============================================================

def notification_save(api_key: str, notification_type: str, message: str) -> bool:
    try:
        _db().table("notifications").insert({
            "api_key": api_key,
            "type": notification_type[:50],
            "message": message[:500],
            "read": False
        }).execute()
        return True
    except Exception as e:
        log_error(str(e), context="notification_save")
        return False


def notification_get_all(api_key: str, unread_only: bool = False, limit: int = 50) -> List[Dict]:
    try:
        q = db.table("notifications").select("*").eq("api_key", api_key)
        if unread_only:
            q = q.eq("read", False)
        result = q.order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception:
        return []


def notification_mark_read(notification_id: str) -> bool:
    try:
        _db().table("notifications").update({"read": True}).eq("id", notification_id).execute()
        return True
    except Exception:
        return False


def notification_mark_all_read(api_key: str) -> bool:
    try:
        _db().table("notifications").update({"read": True}).eq("api_key", api_key).eq("read", False).execute()
        return True
    except Exception:
        return False


def notification_count_unread(api_key: str) -> int:
    try:
        result = db.table("notifications").select("id", count="exact").eq("api_key", api_key).eq("read", False).execute()
        return result.count or 0
    except Exception:
        return 0


def notification_delete(notification_id: str, api_key: str) -> bool:
    try:
        _db().table("notifications").delete().eq("id", notification_id).eq("api_key", api_key).execute()
        return True
    except Exception:
        return False


# ============================================================
# WEBHOOKS
# ============================================================

def webhook_save(api_key: str, url: str, events: list) -> bool:
    try:
        _db().table("webhooks").insert({
            "api_key": api_key,
            "url": url[:2000],
            "events": str(events)[:500],
            "active": True,
            "trigger_count": 0
        }).execute()
        return True
    except Exception as e:
        log_error(str(e), context="webhook_save")
        return False


def webhook_get_all(api_key: str) -> List[Dict]:
    try:
        result = db.table("webhooks").select("*").eq("api_key", api_key).eq("active", True).execute()
        return result.data or []
    except Exception:
        return []


def webhook_delete(webhook_id: str, api_key: str) -> bool:
    try:
        _db().table("webhooks").update({"active": False}).eq("id", webhook_id).eq("api_key", api_key).execute()
        return True
    except Exception:
        return False


def webhook_increment_trigger(webhook_id: str) -> None:
    try:
        existing = db.table("webhooks").select("trigger_count").eq("id", webhook_id).execute()
        if existing.data:
            count = existing.data[0].get("trigger_count", 0) + 1
            _db().table("webhooks").update({
                "trigger_count": count,
                "last_triggered": datetime.utcnow().isoformat()
            }).eq("id", webhook_id).execute()
    except Exception:
        pass


# ============================================================
# MEMORY STATISTICS
# ============================================================

def memory_stats_increment_total(api_key: str) -> None:
    try:
        existing = db.table("memory_stats").select("total_ever").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0].get("total_ever", 0)
            _db().table("memory_stats").update({
                "total_ever": current + 1,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("api_key", api_key).execute()
        else:
            _db().table("memory_stats").insert({
                "api_key": api_key,
                "total_ever": 1,
                "deleted_count": 0
            }).execute()
    except Exception:
        pass


def memory_stats_increment_deleted(api_key: str) -> None:
    try:
        existing = db.table("memory_stats").select("deleted_count").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0].get("deleted_count", 0)
            _db().table("memory_stats").update({
                "deleted_count": current + 1,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("api_key", api_key).execute()
    except Exception:
        pass


def memory_stats_get(api_key: str) -> Dict:
    try:
        stats = db.table("memory_stats").select("*").eq("api_key", api_key).execute()
        active = db.table("memories").select("id", count="exact").eq("api_key", api_key).execute()
        if stats.data:
            return {
                "active": active.count or 0,
                "total_ever": stats.data[0].get("total_ever", 0),
                "deleted": stats.data[0].get("deleted_count", 0),
                "auto_delete_days": 90
            }
        return {"active": active.count or 0, "total_ever": 0, "deleted": 0, "auto_delete_days": 90}
    except Exception:
        return {"active": 0, "total_ever": 0, "deleted": 0, "auto_delete_days": 90}
