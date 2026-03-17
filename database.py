import os
from typing import Optional
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
        result = db.table("users").insert({
            "email": email.lower().strip(),
            "password": password_hash,
            "api_key_1": key1,
            "api_key_2": key2
        }).execute()
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


def user_delete(user_id):
    try:
        db.table("users").delete().eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_delete")
        return False


def user_update_email(user_id, new_email):
    try:
        db.table("users").update({"email": new_email.lower().strip()}).eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_update_email")
        return False


def user_update_password(user_id, new_hash):
    try:
        db.table("users").update({"password": new_hash}).eq("id", user_id).execute()
        return True
    except Exception as e:
        log_error(str(e), context="user_update_password")
        return False


def memory_insert(content, user_id, api_key):
    try:
        result = db.table("memories").insert({
            "content": content,
            "user_id": user_id,
            "api_key": api_key
        }).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        log_error(str(e), context="memory_insert")
        return {"error": str(e)}


def memory_search(query, user_id, api_key, limit=5):
    try:
        result = db.table("memories").select("*").eq("api_key", api_key).eq("user_id", user_id).ilike("content", f"%{query}%").order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        log_error(str(e), context="memory_search")
        return []


def memory_search_all_users(query, api_key, limit=10):
    try:
        result = db.table("memories").select("*").eq("api_key", api_key).ilike("content", f"%{query}%").order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        log_error(str(e), context="memory_search_all_users")
        return []


def memory_delete(memory_id, api_key):
    try:
        db.table("memories").delete().eq("id", memory_id).eq("api_key", api_key).execute()
        return True
    except Exception as e:
        log_error(str(e), context="memory_delete")
        return False


def memory_delete_by_user(user_id, api_key):
    try:
        db.table("memories").delete().eq("user_id", user_id).eq("api_key", api_key).execute()
        return True
    except Exception as e:
        log_error(str(e), context="memory_delete_by_user")
        return False


def memory_get_all(api_key, user_id=None):
    try:
        q = db.table("memories").select("*").eq("api_key", api_key)
        if user_id:
            q = q.eq("user_id", user_id)
        result = q.order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        log_error(str(e), context="memory_get_all")
        return []


def memory_get_recent(api_key, limit=50):
    try:
        result = db.table("memories").select("*").eq("api_key", api_key).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        log_error(str(e), context="memory_get_recent")
        return []


def memory_count_active(api_key):
    try:
        result = db.table("memories").select("id", count="exact").eq("api_key", api_key).execute()
        return result.count or 0
    except Exception:
        return 0


def memory_count_by_user(api_key, user_id):
    try:
        result = db.table("memories").select("id", count="exact").eq("api_key", api_key).eq("user_id", user_id).execute()
        return result.count or 0
    except Exception:
        return 0


def memory_stats_get(api_key):
    try:
        result = db.table("memory_stats").select("*").eq("api_key", api_key).execute()
        if result.data:
            return result.data[0]
        return {"total_ever": 0, "deleted_count": 0}
    except Exception:
        return {"total_ever": 0, "deleted_count": 0}


def memory_stats_increment(api_key):
    try:
        existing = db.table("memory_stats").select("total_ever").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0]["total_ever"]
            db.table("memory_stats").update({"total_ever": current + 1}).eq("api_key", api_key).execute()
        else:
            db.table("memory_stats").insert({"api_key": api_key, "total_ever": 1, "deleted_count": 0}).execute()
    except Exception as e:
        log_error(str(e), context="memory_stats_increment")


def memory_stats_increment_deleted(api_key):
    try:
        existing = db.table("memory_stats").select("deleted_count").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0]["deleted_count"]
            db.table("memory_stats").update({"deleted_count": current + 1}).eq("api_key", api_key).execute()
    except Exception as e:
        log_error(str(e), context="memory_stats_increment_deleted")


def usage_log(api_key, layer, endpoint):
    try:
        db.table("usage").insert({"api_key": api_key, "layer": layer, "endpoint": endpoint}).execute()
    except Exception as e:
        log_error(str(e), context="usage_log")


def usage_count_today(api_key):
    try:
        from datetime import date
        today = str(date.today())
        result = db.table("usage").select("id", count="exact").eq("api_key", api_key).gte("created_at", today).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_count_total(api_key):
    try:
        result = db.table("usage").select("id", count="exact").eq("api_key", api_key).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_count_by_layer(api_key, layer):
    try:
        result = db.table("usage").select("id", count="exact").eq("api_key", api_key).eq("layer", layer).execute()
        return result.count or 0
    except Exception:
        return 0


def usage_by_layer(api_key):
    try:
        result = db.table("usage").select("layer").eq("api_key", api_key).execute()
        layer_counts = {}
        for row in (result.data or []):
            l = row["layer"]
            layer_counts[l] = layer_counts.get(l, 0) + 1
        return [{"layer": k, "count": v} for k, v in sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)]
    except Exception:
        return []


def usage_get_timeline(api_key, days=30):
    try:
        from datetime import date, timedelta
        start = str(date.today() - timedelta(days=days))
        result = db.table("usage").select("created_at").eq("api_key", api_key).gte("created_at", start).execute()
        daily = {}
        for row in (result.data or []):
            day = str(row["created_at"])[:10]
            daily[day] = daily.get(day, 0) + 1
        return [{"date": k, "count": v} for k, v in sorted(daily.items())]
    except Exception:
        return []


def threat_log(api_key, threat_type, content):
    try:
        db.table("threats").insert({"api_key": api_key, "threat_type": threat_type, "content": content[:200]}).execute()
    except Exception as e:
        log_error(str(e), context="threat_log")


def threat_get_all(api_key):
    try:
        result = db.table("threats").select("*").eq("api_key", api_key).order("created_at", desc=True).limit(50).execute()
        return result.data or []
    except Exception:
        return []


def threat_count_today(api_key):
    try:
        from datetime import date
        today = str(date.today())
        result = db.table("threats").select("id", count="exact").eq("api_key", api_key).gte("created_at", today).execute()
        return result.count or 0
    except Exception:
        return 0


def threat_count_total(api_key):
    try:
        result = db.table("threats").select("id", count="exact").eq("api_key", api_key).execute()
        return result.count or 0
    except Exception:
        return 0


def threat_get_by_type(api_key, threat_type):
    try:
        result = db.table("threats").select("*").eq("api_key", api_key).eq("threat_type", threat_type).order("created_at", desc=True).limit(20).execute()
        return result.data or []
    except Exception:
        return []


def cache_get(question_hash):
    try:
        result = db.table("cache").select("response").eq("question_hash", question_hash).execute()
        if result.data:
            return result.data[0]["response"]
        return None
    except Exception:
        return None


def cache_set(question_hash, response):
    try:
        db.table("cache").upsert({"question_hash": question_hash, "response": response}).execute()
    except Exception as e:
        log_error(str(e), context="cache_set")


def cache_delete(question_hash):
    try:
        db.table("cache").delete().eq("question_hash", question_hash).execute()
        return True
    except Exception:
        return False


def cache_stats_get(api_key):
    try:
        result = db.table("cache_stats").select("*").eq("api_key", api_key).execute()
        if result.data:
            return result.data[0]
        return {"hit_count": 0, "miss_count": 0}
    except Exception:
        return {"hit_count": 0, "miss_count": 0}


def cache_stats_increment_hit(api_key):
    try:
        existing = db.table("cache_stats").select("hit_count").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0]["hit_count"]
            db.table("cache_stats").update({"hit_count": current + 1}).eq("api_key", api_key).execute()
        else:
            db.table("cache_stats").insert({"api_key": api_key, "hit_count": 1, "miss_count": 0}).execute()
    except Exception as e:
        log_error(str(e), context="cache_hit")


def cache_stats_increment_miss(api_key):
    try:
        existing = db.table("cache_stats").select("miss_count").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0]["miss_count"]
            db.table("cache_stats").update({"miss_count": current + 1}).eq("api_key", api_key).execute()
    except Exception as e:
        log_error(str(e), context="cache_miss")


def incident_log(api_key, description):
    try:
        result = db.table("incidents").insert({"api_key": api_key, "description": description, "recovered": False}).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        log_error(str(e), context="incident_log")
        return {"error": str(e)}


def incident_resolve(incident_id):
    try:
        db.table("incidents").update({"recovered": True}).eq("id", incident_id).execute()
    except Exception as e:
        log_error(str(e), context="incident_resolve")


def incident_get_all(api_key):
    try:
        result = db.table("incidents").select("*").eq("api_key", api_key).order("created_at", desc=True).limit(20).execute()
        return result.data or []
    except Exception:
        return []


def incident_count_unresolved(api_key):
    try:
        result = db.table("incidents").select("id", count="exact").eq("api_key", api_key).eq("recovered", False).execute()
        return result.count or 0
    except Exception:
        return 0


def analytics_log(api_key, user_id, question, response_length, response_time):
    try:
        db.table("analytics").insert({
            "api_key": api_key,
            "user_id": user_id,
            "question": question[:300],
            "response_length": response_length,
            "response_time": round(response_time, 3)
        }).execute()
    except Exception as e:
        log_error(str(e), context="analytics_log")


def analytics_get_stats(api_key):
    try:
        total = db.table("analytics").select("id", count="exact").eq("api_key", api_key).execute()
        questions = db.table("analytics").select("question, response_time").eq("api_key", api_key).limit(500).execute()
        rows = questions.data or []
        avg_time = 0.0
        if rows:
            times = [r["response_time"] for r in rows if r.get("response_time")]
            avg_time = round(sum(times) / len(times), 3) if times else 0.0
        return {
            "total_tracked": total.count or 0,
            "questions": [r["question"] for r in rows if r.get("question")],
            "avg_response_time": avg_time
        }
    except Exception:
        return {"total_tracked": 0, "questions": [], "avg_response_time": 0}


def analytics_get_unique_users(api_key):
    try:
        result = db.table("analytics").select("user_id").eq("api_key", api_key).execute()
        users = set(r["user_id"] for r in (result.data or []) if r.get("user_id"))
        return len(users)
    except Exception:
        return 0


def analytics_get_peak_hours(api_key):
    try:
        result = db.table("analytics").select("created_at").eq("api_key", api_key).limit(1000).execute()
        hours = {}
        for row in (result.data or []):
            if row.get("created_at"):
                hour = str(row["created_at"])[11:13]
                hours[hour] = hours.get(hour, 0) + 1
        return sorted(hours.items(), key=lambda x: x[1], reverse=True)[:5]
    except Exception:
        return []


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
        return {"average_score": avg, "total_tracked": len(scores), "trend": trend, "recent_avg": round(sum(recent) / len(recent), 1) if recent else 0}
    except Exception:
        return {"average_score": 0, "total_tracked": 0, "trend": "error"}


def genome_save(api_key, profile):
    try:
        existing = db.table("genome_profiles").select("id").eq("api_key", api_key).execute()
        if existing.data:
            db.table("genome_profiles").update({"profile": str(profile)}).eq("api_key", api_key).execute()
        else:
            db.table("genome_profiles").insert({"api_key": api_key, "profile": str(profile)}).execute()
        return True
    except Exception as e:
        log_error(str(e), context="genome_save")
        return False


def genome_get(api_key):
    try:
        result = db.table("genome_profiles").select("profile").eq("api_key", api_key).execute()
        if result.data:
            import ast
            return ast.literal_eval(result.data[0]["profile"])
        return None
    except Exception:
        return None


def nexus_source_save(api_key, source_type, config):
    try:
        db.table("nexus_sources").insert({"api_key": api_key, "source_type": source_type, "config": str(config), "active": True}).execute()
        return True
    except Exception as e:
        log_error(str(e), context="nexus_source_save")
        return False


def nexus_sources_get(api_key):
    try:
        result = db.table("nexus_sources").select("*").eq("api_key", api_key).eq("active", True).execute()
        return result.data or []
    except Exception:
        return []


def oracle_log(api_key, user_id, original, predicted):
    try:
        db.table("oracle_predictions").insert({"api_key": api_key, "user_id": user_id, "original_message": original[:300], "predicted_intent": predicted[:500]}).execute()
    except Exception as e:
        log_error(str(e), context="oracle_log")


def oracle_get_history(api_key, user_id):
    try:
        result = db.table("oracle_predictions").select("*").eq("api_key", api_key).eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
        return result.data or []
    except Exception:
        return []


def interaction_log(api_key, user_id, layer, input_text, output_text):
    try:
        db.table("layer_interactions").insert({"api_key": api_key, "user_id": user_id, "layer": layer, "input_text": input_text[:200], "output_text": output_text[:500]}).execute()
    except Exception as e:
        log_error(str(e), context="interaction_log")


def interaction_get_by_user(api_key, user_id, limit=50):
    try:
        result = db.table("layer_interactions").select("*").eq("api_key", api_key).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception:
        return []


def notification_save(api_key, notification_type, message, read=False):
    try:
        db.table("notifications").insert({"api_key": api_key, "type": notification_type, "message": message, "read": read}).execute()
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


def export_get_all_data(api_key):
    try:
        memories = memory_get_all(api_key)
        analytics = analytics_get_stats(api_key)
        threats = threat_get_all(api_key)
        incidents = incident_get_all(api_key)
        usage_data = usage_by_layer(api_key)
        return {
            "memories": memories,
            "analytics": analytics,
            "threats": threats,
            "incidents": incidents,
            "usage_by_layer": usage_data,
            "total_memories": len(memories),
            "total_threats": len(threats),
            "total_incidents": len(incidents)
        }
    except Exception as e:
        log_error(str(e), context="export_get_all_data")
        return {}


def admin_get_global_stats():
    try:
        users = db.table("users").select("id", count="exact").execute()
        memories = db.table("memories").select("id", count="exact").execute()
        usage = db.table("usage").select("id", count="exact").execute()
        threats = db.table("threats").select("id", count="exact").execute()
        return {
            "total_users": users.count or 0,
            "total_memories": memories.count or 0,
            "total_api_calls": usage.count or 0,
            "total_threats_blocked": threats.count or 0
        }
    except Exception:
        return {"total_users": 0, "total_memories": 0, "total_api_calls": 0, "total_threats_blocked": 0}


def admin_get_user_breakdown():
    try:
        users = user_get_all()
        breakdown = []
        for user in users[:100]:
            api_key = user.get("api_key_1", "")
            breakdown.append({
                "email": user.get("email", "")[:30],
                "active_memories": memory_count_active(api_key),
                "total_calls": usage_count_total(api_key),
                "threats_blocked": threat_count_total(api_key),
                "joined": str(user.get("created_at", ""))[:10]
            })
        return breakdown
    except Exception:
        return []


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
