import os
from supabase import create_client, Client
from dotenv import load_dotenv
from config import SUPABASE_URL, SUPABASE_KEY
from logger import log_error

load_dotenv()

try:
    db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    log_error(f"Database connection failed: {e}", context="startup")
    db = None


def get_db():
    return db


def user_create(email, password_hash, key1, key2):
    try:
        result = db.table("users").insert({"email": email.lower().strip(), "password": password_hash, "api_key_1": key1, "api_key_2": key2}).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        log_error(str(e), context="user_create")
        return {"error": str(e)}


def user_get_by_email(email):
    try:
        result = db.table("users").select("*").eq("email", email.lower().strip()).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        log_error(str(e), context="user_get_by_email")
        return None


def user_get_by_key(api_key):
    try:
        r1 = db.table("users").select("*").eq("api_key_1", api_key).execute()
        if r1.data:
            return r1.data[0]
        r2 = db.table("users").select("*").eq("api_key_2", api_key).execute()
        return r2.data[0] if r2.data else None
    except Exception as e:
        log_error(str(e), context="user_get_by_key")
        return None


def user_update_key(user_id, key_number, new_key):
    try:
        db.table("users").update({f"api_key_{key_number}": new_key}).eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_update_key")
        return False


def user_update_password(user_id, new_hash):
    try:
        db.table("users").update({"password": new_hash}).eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_update_password")
        return False


def user_delete(user_id):
    try:
        db.table("users").delete().eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_delete")
        return False


def user_get_all():
    try:
        result = db.table("users").select("id, email, api_key_1, api_key_2, created_at").order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        log_error(str(e), context="user_get_all")
        return []


def user_count():
    try:
        result = db.table("users").select("id", count="exact").execute()
        return result.count or 0
    except Exception:
        return 0


def usage_log(api_key, layer, endpoint):
    try:
        db.table("nexus_usage").insert({"api_key": api_key, "layer": layer, "endpoint": endpoint}).execute()
    except Exception as e:
        log_error(str(e), context="usage_log")


def usage_count_today(api_key):
    try:
        from datetime import date
        today = str(date.today())
        result = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).gte("created_at", today).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_count_total(api_key):
    try:
        result = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_by_layer(api_key):
    try:
        result = db.table("nexus_usage").select("layer").eq("api_key", api_key).execute()
        layer_counts = {}
        for row in (result.data or []):
            l = row["layer"]
            layer_counts[l] = layer_counts.get(l, 0) + 1
        return [{"layer": k, "count": v} for k, v in sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)]
    except Exception:
        return []


def admin_get_global_stats():
    try:
        users = db.table("users").select("id", count="exact").execute()
        memories = db.table("memories").select("id", count="exact").execute()
        usage = db.table("nexus_usage").select("id", count="exact").execute()
        threats = db.table("aegis_threats").select("id", count="exact").execute()
        return {
            "total_users": users.count or 0,
            "total_memories": memories.count or 0,
            "total_api_calls": usage.count or 0,
            "total_threats_blocked": threats.count or 0
        }
    except Exception:
        return {"total_users": 0, "total_memories": 0, "total_api_calls": 0, "total_threats_blocked": 0}


def evolve_log(api_key, question, response, score):
    try:
        db.table("evolve_data").insert({"api_key": api_key, "question": question[:300], "response": response[:600], "score": score}).execute()
    except Exception as e:
        log_error(str(e), context="evolve_log")


def evolve_get_performance(api_key):
    try:
        result = db.table("evolve_data").select("score, created_at").eq("api_key", api_key).order("created_at", desc=True).limit(100).execute()
        if not result.data:
            return {"average_score": 0, "total_tracked": 0, "trend": "no_data"}
        scores = [r["score"] for r in result.data if r.get("score") is not None]
        if not scores:
            return {"average_score": 0, "total_tracked": 0, "trend": "no_data"}
        avg = round(sum(scores) / len(scores), 1)
        recent = scores[:10]
        older = scores[10:20] if len(scores) > 10 else scores
        trend = "stable"
        if older and recent:
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            if recent_avg > older_avg + 2:
                trend = "improving"
            elif recent_avg < older_avg - 2:
                trend = "declining"
        return {"average_score": avg, "total_tracked": len(scores), "trend": trend}
    except Exception:
        return {"average_score": 0, "total_tracked": 0, "trend": "error"}


def notification_save(api_key, notification_type, message):
    try:
        db.table("notifications").insert({"api_key": api_key, "type": notification_type, "message": message, "read": False}).execute()
        return True
    except Exception as e:
        log_error(str(e), context="notification_save")
        return False


def notification_get_all(api_key, unread_only=False):
    try:
        q = db.table("notifications").select("*").eq("api_key", api_key)
        if unread_only:
            q = q.eq("read", False)
        result = q.order("created_at", desc=True).limit(50).execute()
        return result.data or []
    except Exception:
        return []


def notification_mark_read(notification_id):
    try:
        db.table("notifications").update({"read": True}).eq("id", notification_id).execute()
        return True
    except Exception:
        return False


def notification_count_unread(api_key):
    try:
        result = db.table("notifications").select("id", count="exact").eq("api_key", api_key).eq("read", False).execute()
        return result.count or 0
    except Exception:
        return 0


def webhook_save(api_key, url, events):
    try:
        db.table("webhooks").insert({"api_key": api_key, "url": url, "events": str(events), "active": True}).execute()
        return True
    except Exception as e:
        log_error(str(e), context="webhook_save")
        return False


def webhook_get_all(api_key):
    try:
        result = db.table("webhooks").select("*").eq("api_key", api_key).eq("active", True).execute()
        return result.data or []
    except Exception:
        return []


def webhook_delete(webhook_id, api_key):
    try:
        db.table("webhooks").update({"active": False}).eq("id", webhook_id).eq("api_key", api_key).execute()
        return True
    except Exception:
        return False
