import hashlib
import time
import re
from datetime import datetime, date, timedelta
from typing import Optional


def nexus_remember(content, user_id, api_key, db, tags=None):
    try:
        if not content or not user_id:
            return {"status": "error", "message": "content and user_id required", "pillar": "NEXUS_CORE", "layer": "MEMEX"}
        if len(content) > 5000:
            return {"status": "error", "message": "content too long. max 5000 characters", "pillar": "NEXUS_CORE", "layer": "MEMEX"}
        content = content.replace('\x00', '').strip()
        user_id = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        if tags and isinstance(tags, list):
            tag_str = " [TAGS:" + ",".join(str(t)[:30] for t in tags[:10]) + "]"
            content_stored = content + tag_str
        else:
            content_stored = content
        result = db.table("memories").insert({
            "content": content_stored,
            "user_id": user_id,
            "api_key": api_key
        }).execute()
        if result.data:
            nexus_increment_total(api_key, db)
            db.table("nexus_usage").insert({"api_key": api_key, "layer": "MEMEX", "action": "remember"}).execute()
            return {"status": "stored", "id": result.data[0].get("id", ""), "preview": content[:80], "layer": "MEMEX", "pillar": "NEXUS_CORE"}
        return {"status": "error", "message": "failed to store", "layer": "MEMEX"}
    except Exception as e:
        return {"status": "error", "message": "storage failed", "layer": "MEMEX"}


def nexus_recall(query, user_id, api_key, db, limit=5):
    try:
        if not query or not user_id:
            return {"status": "error", "message": "query and user_id required", "layer": "MEMEX"}
        limit = max(1, min(limit, 20))
        query = query.strip()[:10000]
        user_id = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        result = db.table("memories").select("*").eq("api_key", api_key).eq("user_id", user_id).ilike("content", f"%{query}%").order("created_at", desc=True).limit(limit).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "MEMEX", "action": "recall"}).execute()
        return {"status": "success", "memories": result.data or [], "count": len(result.data or []), "query": query, "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "recall failed", "layer": "MEMEX"}


def nexus_recall_global(query, api_key, db, limit=10):
    try:
        if not query:
            return {"status": "error", "message": "query required", "layer": "MEMEX"}
        limit = max(1, min(limit, 20))
        result = db.table("memories").select("*").eq("api_key", api_key).ilike("content", f"%{query}%").order("created_at", desc=True).limit(limit).execute()
        return {"status": "success", "memories": result.data or [], "count": len(result.data or []), "scope": "all_users", "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "global recall failed", "layer": "MEMEX"}


def nexus_forget(memory_id, api_key, db):
    try:
        if not memory_id:
            return {"status": "error", "message": "memory_id required", "layer": "MEMEX"}
        db.table("memories").delete().eq("id", memory_id).eq("api_key", api_key).execute()
        nexus_increment_deleted(api_key, db)
        return {"status": "deleted", "id": memory_id, "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "delete failed", "layer": "MEMEX"}


def nexus_forget_user(user_id, api_key, db):
    try:
        if not user_id:
            return {"status": "error", "message": "user_id required", "layer": "MEMEX"}
        user_id = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        count_result = db.table("memories").select("id", count="exact").eq("api_key", api_key).eq("user_id", user_id).execute()
        count = count_result.count or 0
        db.table("memories").delete().eq("api_key", api_key).eq("user_id", user_id).execute()
        return {"status": "deleted", "user_id": user_id, "deleted_count": count, "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "user delete failed", "layer": "MEMEX"}


def nexus_get_all_memories(api_key, db, user_id=None):
    try:
        q = db.table("memories").select("*").eq("api_key", api_key)
        if user_id:
            user_id = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
            q = q.eq("user_id", user_id)
        result = q.order("created_at", desc=True).execute()
        stats = nexus_get_memory_stats(api_key, db)
        return {"status": "success", "memories": result.data or [], "active_count": stats.get("active", 0), "total_ever": stats.get("total_ever", 0), "deleted_count": stats.get("deleted", 0), "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "get all failed", "layer": "MEMEX"}


def nexus_get_memory_stats(api_key, db):
    try:
        active = db.table("memories").select("id", count="exact").eq("api_key", api_key).execute()
        stats = db.table("memory_stats").select("*").eq("api_key", api_key).execute()
        if stats.data:
            total_ever = stats.data[0].get("total_ever", 0)
            deleted = stats.data[0].get("deleted_count", 0)
        else:
            total_ever = 0
            deleted = 0
        return {"active": active.count or 0, "total_ever": total_ever, "deleted": deleted, "auto_delete_days": 90, "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"active": 0, "total_ever": 0, "deleted": 0}


def nexus_bulk_remember(items, api_key, db):
    try:
        if not isinstance(items, list) or len(items) == 0:
            return {"status": "error", "message": "items must be non-empty list", "layer": "MEMEX"}
        if len(items) > 50:
            return {"status": "error", "message": "max 50 items per bulk operation", "layer": "MEMEX"}
        stored = 0
        errors = 0
        ids = []
        for item in items:
            if not isinstance(item, dict):
                errors += 1
                continue
            content = item.get("content", "")
            user_id = item.get("user_id", "")
            if not content or not user_id or len(content) > 5000:
                errors += 1
                continue
            result = nexus_remember(content, user_id, api_key, db)
            if result.get("status") == "stored":
                stored += 1
                ids.append(result.get("id", ""))
            else:
                errors += 1
        return {"status": "completed", "stored": stored, "errors": errors, "ids": ids, "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "bulk operation failed", "layer": "MEMEX"}


def nexus_search_by_tag(tag, api_key, db, user_id=None, limit=10):
    try:
        if not tag:
            return {"status": "error", "message": "tag required", "layer": "MEMEX"}
        limit = max(1, min(limit, 20))
        tag_query = f"TAGS:{tag}"
        q = db.table("memories").select("*").eq("api_key", api_key).ilike("content", f"%{tag_query}%")
        if user_id:
            user_id = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
            q = q.eq("user_id", user_id)
        result = q.limit(limit).execute()
        return {"status": "success", "tag": tag, "memories": result.data or [], "count": len(result.data or []), "layer": "MEMEX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "tag search failed", "layer": "MEMEX"}


def nexus_increment_total(api_key, db):
    try:
        existing = db.table("memory_stats").select("total_ever").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0]["total_ever"]
            db.table("memory_stats").update({"total_ever": current + 1}).eq("api_key", api_key).execute()
        else:
            db.table("memory_stats").insert({"api_key": api_key, "total_ever": 1, "deleted_count": 0}).execute()
    except Exception:
        pass


def nexus_increment_deleted(api_key, db):
    try:
        existing = db.table("memory_stats").select("deleted_count").eq("api_key", api_key).execute()
        if existing.data:
            current = existing.data[0]["deleted_count"]
            db.table("memory_stats").update({"deleted_count": current + 1}).eq("api_key", api_key).execute()
    except Exception:
        pass


def flux_check_cache(question, api_key, db):
    try:
        if not question:
            return {"hit": False, "layer": "FLUX", "pillar": "NEXUS_CORE"}
        if len(question) > 10000:
            return {"hit": False, "layer": "FLUX"}
        qhash = hashlib.sha256(question.lower().strip().encode()).hexdigest()[:32]
        result = db.table("flux_cache").select("response").eq("question_hash", qhash).execute()
        if result.data:
            db.table("flux_stats").select("hit_count").eq("api_key", api_key).execute()
            existing = db.table("flux_stats").select("hit_count").eq("api_key", api_key).execute()
            if existing.data:
                db.table("flux_stats").update({"hit_count": existing.data[0]["hit_count"] + 1}).eq("api_key", api_key).execute()
            else:
                db.table("flux_stats").insert({"api_key": api_key, "hit_count": 1, "miss_count": 0}).execute()
            db.table("nexus_usage").insert({"api_key": api_key, "layer": "FLUX", "action": "cache_hit"}).execute()
            return {"hit": True, "response": result.data[0]["response"], "speed_ms": 0, "layer": "FLUX", "pillar": "NEXUS_CORE"}
        existing = db.table("flux_stats").select("miss_count").eq("api_key", api_key).execute()
        if existing.data:
            db.table("flux_stats").update({"miss_count": existing.data[0]["miss_count"] + 1}).eq("api_key", api_key).execute()
        return {"hit": False, "layer": "FLUX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"hit": False, "layer": "FLUX"}


def flux_store_cache(question, response, api_key, db):
    try:
        if not question or not response:
            return {"status": "error", "message": "question and response required", "layer": "FLUX"}
        if len(question) > 10000:
            return {"status": "error", "message": "question too long", "layer": "FLUX"}
        if len(response) > 50000:
            return {"status": "skipped", "reason": "response too large to cache", "layer": "FLUX"}
        qhash = hashlib.sha256(question.lower().strip().encode()).hexdigest()[:32]
        db.table("flux_cache").upsert({"question_hash": qhash, "response": response}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "FLUX", "action": "cache_store"}).execute()
        return {"status": "cached", "layer": "FLUX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "cache store failed", "layer": "FLUX"}


def flux_invalidate(question, api_key, db):
    try:
        if not question:
            return {"status": "error", "message": "question required", "layer": "FLUX"}
        qhash = hashlib.sha256(question.lower().strip().encode()).hexdigest()[:32]
        db.table("flux_cache").delete().eq("question_hash", qhash).execute()
        return {"status": "invalidated", "layer": "FLUX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "invalidate failed", "layer": "FLUX"}


def flux_get_stats(api_key, db):
    try:
        result = db.table("flux_stats").select("*").eq("api_key", api_key).execute()
        if result.data:
            hits = result.data[0].get("hit_count", 0)
            misses = result.data[0].get("miss_count", 0)
            total = hits + misses
            hit_rate = round((hits / total) * 100, 1) if total > 0 else 0
            return {"total_cache_hits": hits, "total_cache_misses": misses, "hit_rate_percent": hit_rate, "total_requests": total, "layer": "FLUX", "pillar": "NEXUS_CORE"}
        return {"total_cache_hits": 0, "total_cache_misses": 0, "hit_rate_percent": 0, "total_requests": 0, "layer": "FLUX"}
    except Exception as e:
        return {"total_cache_hits": 0, "total_cache_misses": 0, "layer": "FLUX"}


def flux_warm_cache(items, api_key, db):
    try:
        if not isinstance(items, list):
            return {"status": "error", "message": "items must be a list", "layer": "FLUX"}
        if len(items) > 100:
            return {"status": "error", "message": "max 100 items per warm", "layer": "FLUX"}
        cached = 0
        skipped = 0
        for item in items:
            if not isinstance(item, dict):
                skipped += 1
                continue
            q = item.get("question", "")
            r = item.get("response", "")
            if not q or not r:
                skipped += 1
                continue
            result = flux_store_cache(q, r, api_key, db)
            if result.get("status") == "cached":
                cached += 1
            else:
                skipped += 1
        return {"status": "complete", "cached": cached, "skipped": skipped, "layer": "FLUX", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "warm failed", "layer": "FLUX"}


def pulse_health_check(db):
    start = time.time()
    try:
        db.table("users").select("id").limit(1).execute()
        response_ms = round((time.time() - start) * 1000, 2)
        status = "healthy"
        if response_ms > 2000:
            status = "degraded"
        elif response_ms > 5000:
            status = "unhealthy"
        return {"status": status, "database": "connected", "response_ms": response_ms, "layer": "PULSE", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "response_ms": -1, "error": "database unreachable", "layer": "PULSE", "pillar": "NEXUS_CORE"}


def pulse_report_incident(api_key, description, db, severity="medium"):
    try:
        if not description:
            return {"status": "error", "message": "description required", "layer": "PULSE"}
        if len(description) > 1000:
            return {"status": "error", "message": "description too long", "layer": "PULSE"}
        valid_severities = ["low", "medium", "high", "critical"]
        if severity not in valid_severities:
            severity = "medium"
        result = db.table("pulse_incidents").insert({"api_key": api_key, "description": f"[{severity.upper()}] {description}", "recovered": False}).execute()
        if result.data:
            return {"status": "logged", "id": result.data[0].get("id", ""), "severity": severity, "layer": "PULSE", "pillar": "NEXUS_CORE"}
        return {"status": "error", "message": "failed to log", "layer": "PULSE"}
    except Exception as e:
        return {"status": "error", "message": "incident log failed", "layer": "PULSE"}


def pulse_resolve_incident(incident_id, api_key, db):
    try:
        if not incident_id:
            return {"status": "error", "message": "incident_id required", "layer": "PULSE"}
        db.table("pulse_incidents").update({"recovered": True}).eq("id", incident_id).eq("api_key", api_key).execute()
        return {"status": "resolved", "id": incident_id, "layer": "PULSE", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "resolve failed", "layer": "PULSE"}


def pulse_get_health_report(api_key, db):
    try:
        health = pulse_health_check(db)
        incidents = db.table("pulse_incidents").select("*").eq("api_key", api_key).order("created_at", desc=True).limit(20).execute()
        incident_list = incidents.data or []
        resolved = sum(1 for i in incident_list if i.get("recovered"))
        unresolved = len(incident_list) - resolved
        uptime_score = max(0, 100 - (unresolved * 10))
        by_severity = {}
        for inc in incident_list:
            desc = inc.get("description", "")
            if "[CRITICAL]" in desc:
                sev = "critical"
            elif "[HIGH]" in desc:
                sev = "high"
            elif "[MEDIUM]" in desc:
                sev = "medium"
            else:
                sev = "low"
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return {"current_health": health, "uptime_score": uptime_score, "total_incidents": len(incident_list), "resolved": resolved, "unresolved": unresolved, "by_severity": by_severity, "recent_incidents": incident_list[:5], "status": "excellent" if uptime_score >= 90 else "good" if uptime_score >= 70 else "needs_attention", "layer": "PULSE", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "health report failed", "layer": "PULSE"}


def pulse_auto_recover(api_key, db):
    try:
        health = pulse_health_check(db)
        if health.get("status") == "healthy":
            return {"status": "no_recovery_needed", "health": health, "layer": "PULSE"}
        incident = db.table("pulse_incidents").insert({"api_key": api_key, "description": f"[HIGH] Auto recovery: {health.get('error', 'system unhealthy')}", "recovered": False}).execute()
        recovery_health = pulse_health_check(db)
        if recovery_health.get("status") == "healthy":
            if incident.data:
                db.table("pulse_incidents").update({"recovered": True}).eq("id", incident.data[0]["id"]).execute()
            return {"status": "recovered", "previous_health": health, "current_health": recovery_health, "layer": "PULSE", "pillar": "NEXUS_CORE"}
        return {"status": "recovery_failed", "health": recovery_health, "layer": "PULSE"}
    except Exception as e:
        return {"status": "error", "message": "auto recover failed", "layer": "PULSE"}


def insight_track(question, response, user_id, api_key, db, response_time=0.0):
    try:
        if not question or not user_id:
            return {"status": "error", "message": "question and user_id required", "layer": "INSIGHT"}
        if len(question) > 10000:
            return {"status": "error", "message": "question too long", "layer": "INSIGHT"}
        user_id = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        db.table("insight_analytics").insert({"api_key": api_key, "user_id": user_id, "question": question[:300], "response_length": len(response), "response_time": round(float(response_time), 3)}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "INSIGHT", "action": "track"}).execute()
        return {"status": "tracked", "layer": "INSIGHT", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "track failed", "layer": "INSIGHT"}


def insight_get_stats(api_key, db):
    try:
        total = db.table("insight_analytics").select("id", count="exact").eq("api_key", api_key).execute()
        questions = db.table("insight_analytics").select("question, response_time").eq("api_key", api_key).limit(500).execute()
        rows = questions.data or []
        avg_time = 0.0
        if rows:
            times = [r["response_time"] for r in rows if r.get("response_time")]
            avg_time = round(sum(times) / len(times), 3) if times else 0.0
        freq = {}
        for r in rows:
            q = r.get("question", "")
            if q:
                key = q[:60].lower().strip()
                freq[key] = freq.get(key, 0) + 1
        top_questions = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
        usage = db.table("nexus_usage").select("layer").eq("api_key", api_key).execute()
        layer_counts = {}
        for row in (usage.data or []):
            l = row.get("layer", "unknown")
            layer_counts[l] = layer_counts.get(l, 0) + 1
        layer_usage = sorted([{"layer": k, "count": v} for k, v in layer_counts.items()], key=lambda x: x["count"], reverse=True)
        today_str = str(date.today())
        today_usage = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).gte("created_at", today_str).execute()
        total_usage = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).execute()
        unique_users = db.table("insight_analytics").select("user_id").eq("api_key", api_key).execute()
        users = set(r["user_id"] for r in (unique_users.data or []) if r.get("user_id"))
        return {"total_tracked": total.count or 0, "total_api_calls": total_usage.count or 0, "calls_today": today_usage.count or 0, "avg_response_time_ms": avg_time, "unique_users": len(users), "top_questions": [{"question": q, "count": c} for q, c in top_questions], "usage_by_layer": layer_usage, "layer": "INSIGHT", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"total_tracked": 0, "total_api_calls": 0, "calls_today": 0, "layer": "INSIGHT"}


def insight_get_growth(api_key, db):
    try:
        recent_start = str(date.today() - timedelta(days=7))
        prev_start = str(date.today() - timedelta(days=14))
        recent = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).gte("created_at", recent_start).execute()
        prev = db.table("nexus_usage").select("id", count="exact").eq("api_key", api_key).gte("created_at", prev_start).lt("created_at", recent_start).execute()
        recent_count = recent.count or 0
        prev_count = prev.count or 0
        if prev_count > 0:
            growth = round(((recent_count - prev_count) / prev_count) * 100, 1)
        else:
            growth = 100 if recent_count > 0 else 0
        trend = "growing" if growth > 5 else "declining" if growth < -5 else "stable"
        return {"growth_rate_percent": growth, "trend": trend, "recent_week": recent_count, "previous_week": prev_count, "layer": "INSIGHT", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"growth_rate_percent": 0, "trend": "unknown", "layer": "INSIGHT"}


def echo_cross_check(response, previous_responses, api_key, db):
    try:
        if not response:
            return {"status": "error", "message": "response required", "layer": "ECHO"}
        if len(response) > 100000:
            return {"status": "error", "message": "response too long", "layer": "ECHO"}
        r_lower = response.lower()
        issues = []
        uncertainty_phrases = ["i think", "i believe", "maybe", "perhaps", "might be", "not sure", "possibly", "could be", "i am not certain"]
        uncertainty_found = [p for p in uncertainty_phrases if p in r_lower]
        if uncertainty_found:
            issues.append({"type": "uncertainty", "detail": f"uncertainty phrases: {uncertainty_found[:3]}", "severity": "low"})
        hallucination_signals = ["as of my knowledge", "if i remember correctly", "i believe the date", "the current price is", "as of today"]
        hallucination_found = [h for h in hallucination_signals if h in r_lower]
        if hallucination_found:
            issues.append({"type": "potential_hallucination", "detail": "possible hallucination signals detected", "severity": "medium"})
        contradiction_pairs = [("yes", "no"), ("true", "false"), ("always", "never"), ("possible", "impossible"), ("available", "unavailable"), ("open", "closed"), ("free", "paid"), ("supported", "not supported")]
        for word_a, word_b in contradiction_pairs:
            if word_a in r_lower and word_b in r_lower:
                issues.append({"type": "internal_contradiction", "detail": f"may contradict itself ({word_a} vs {word_b})", "severity": "high"})
        history_issues = []
        for prev in (previous_responses or [])[-5:]:
            if isinstance(prev, str):
                prev_lower = prev.lower()
                for word_a, word_b in contradiction_pairs:
                    if word_a in r_lower and word_b in prev_lower:
                        history_issues.append({"type": "historical_contradiction", "detail": f"contradicts previous response ({word_a} vs {word_b})", "severity": "high"})
                        break
        all_issues = issues + history_issues
        has_critical = any(i["severity"] == "high" for i in all_issues)
        score = 100
        for issue in all_issues:
            if issue["severity"] == "high":
                score -= 30
            elif issue["severity"] == "medium":
                score -= 15
            else:
                score -= 5
        score = max(0, score)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ECHO", "action": "cross_check"}).execute()
        return {"status": "checked", "is_consistent": not has_critical, "consistency_score": score, "issues_found": len(all_issues), "issues": all_issues, "recommendation": "review_before_sending" if has_critical else "safe_to_send", "layer": "ECHO", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "cross check failed", "layer": "ECHO"}


def echo_verify_factual(statement, context, api_key, db):
    try:
        if not statement or not context:
            return {"status": "error", "message": "statement and context required", "layer": "ECHO"}
        s_lower = statement.lower()
        c_lower = context.lower()
        key_terms = [w for w in s_lower.split() if len(w) > 4]
        matches = sum(1 for term in key_terms if term in c_lower)
        alignment = round((matches / max(len(key_terms), 1)) * 100)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ECHO", "action": "verify_factual"}).execute()
        return {"status": "verified", "alignment_score": alignment, "aligned": alignment > 30, "key_terms_checked": len(key_terms), "terms_found": matches, "layer": "ECHO", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"status": "error", "message": "verify failed", "layer": "ECHO"}


def echo_analyze_quality(response, api_key, db):
    try:
        if not response:
            return {"quality_score": 0, "issues": ["empty response"], "layer": "ECHO"}
        r_lower = response.lower()
        issues = []
        score = 100
        word_count = len(response.split())
        if word_count < 10:
            issues.append("response too short")
            score -= 30
        if word_count > 5000:
            issues.append("response very long")
            score -= 5
        if response.count("?") > 8:
            issues.append("too many questions")
            score -= 15
        uncertainty_words = ["maybe", "perhaps", "possibly", "might", "could be", "i think"]
        uncertainty_count = sum(1 for w in uncertainty_words if w in r_lower)
        if uncertainty_count > 3:
            issues.append("high uncertainty language")
            score -= uncertainty_count * 5
        quality_words = ["solution", "answer", "here is", "you can", "steps", "result"]
        quality_count = sum(1 for w in quality_words if w in r_lower)
        score += min(quality_count * 3, 15)
        score = max(0, min(100, score))
        grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ECHO", "action": "quality_check"}).execute()
        return {"quality_score": score, "grade": grade, "word_count": word_count, "issues": issues, "layer": "ECHO", "pillar": "NEXUS_CORE"}
    except Exception as e:
        return {"quality_score": 0, "issues": ["analysis failed"], "layer": "ECHO"}
