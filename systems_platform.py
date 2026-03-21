import hashlib
import re
from datetime import datetime, date


def neural_bus_publish(topic, payload, api_key, db, publisher_id="", priority="normal"):
    try:
        if not topic or payload is None:
            return {"status": "error", "message": "topic and payload required", "system": "KRONYX_NEURAL_BUS"}
        if len(topic) > 200:
            return {"status": "error", "message": "topic too long", "system": "KRONYX_NEURAL_BUS"}
        topic_clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '', topic)[:200]
        valid_priorities = ["low", "normal", "high", "critical"]
        if priority not in valid_priorities:
            priority = "normal"
        message_id = hashlib.sha256(f"{topic_clean}{str(payload)[:50]}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("neural_bus").insert({"message_id": message_id, "topic": topic_clean, "payload": str(payload)[:2000], "publisher_id": (publisher_id or "")[:100], "priority": priority, "api_key": api_key, "consumed_count": 0}).execute()
        subscribers = db.table("neural_subscriptions").select("subscriber_id").eq("topic", topic_clean).eq("api_key", api_key).eq("active", True).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEURAL_BUS", "endpoint": "publish"}).execute()
        return {"status": "published", "message_id": message_id, "topic": topic_clean, "subscribers_notified": len(subscribers.data or []), "priority": priority, "system": "KRONYX_NEURAL_BUS"}
    except Exception as e:
        return {"status": "error", "message": "publish failed", "system": "KRONYX_NEURAL_BUS"}


def neural_bus_subscribe(topic, subscriber_id, api_key, db):
    try:
        if not topic or not subscriber_id:
            return {"status": "error", "message": "topic and subscriber_id required", "system": "KRONYX_NEURAL_BUS"}
        topic_clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '', topic)[:200]
        subscriber_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', subscriber_id)[:100]
        existing = db.table("neural_subscriptions").select("id").eq("topic", topic_clean).eq("subscriber_id", subscriber_clean).eq("api_key", api_key).execute()
        if existing.data:
            return {"status": "already_subscribed", "topic": topic_clean, "subscriber_id": subscriber_clean, "system": "KRONYX_NEURAL_BUS"}
        db.table("neural_subscriptions").insert({"topic": topic_clean, "subscriber_id": subscriber_clean, "api_key": api_key, "active": True}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEURAL_BUS", "endpoint": "subscribe"}).execute()
        return {"status": "subscribed", "topic": topic_clean, "subscriber_id": subscriber_clean, "system": "KRONYX_NEURAL_BUS"}
    except Exception as e:
        return {"status": "error", "message": "subscribe failed", "system": "KRONYX_NEURAL_BUS"}


def neural_bus_consume(topic, subscriber_id, api_key, db, limit=10):
    try:
        if not topic or not subscriber_id:
            return {"status": "error", "message": "topic and subscriber_id required", "system": "KRONYX_NEURAL_BUS"}
        topic_clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '', topic)[:200]
        limit = min(max(limit, 1), 50)
        result = db.table("neural_bus").select("*").eq("topic", topic_clean).eq("api_key", api_key).order("created_at", desc=True).limit(limit).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEURAL_BUS", "endpoint": "consume"}).execute()
        return {"status": "success", "topic": topic_clean, "messages": result.data or [], "count": len(result.data or []), "system": "KRONYX_NEURAL_BUS"}
    except Exception as e:
        return {"status": "error", "message": "consume failed", "system": "KRONYX_NEURAL_BUS"}


def observatory_track_metric(metric_name, value, api_key, db, ai_id="", dimension="performance", unit=""):
    try:
        if not metric_name or value is None:
            return {"status": "error", "message": "metric_name and value required", "system": "KRONYX_OBSERVATORY"}
        if len(metric_name) > 200:
            return {"status": "error", "message": "metric_name too long", "system": "KRONYX_OBSERVATORY"}
        valid_dimensions = ["performance", "quality", "safety", "usage", "cost", "latency", "accuracy", "satisfaction"]
        if dimension not in valid_dimensions:
            dimension = "performance"
        try:
            value_float = float(value)
        except Exception:
            return {"status": "error", "message": "value must be numeric", "system": "KRONYX_OBSERVATORY"}
        db.table("observatory_metrics").insert({"metric_name": metric_name.replace('\x00', '').strip()[:200], "value": value_float, "ai_id": (ai_id or "")[:100], "dimension": dimension, "unit": (unit or "")[:50], "api_key": api_key}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OBSERVATORY", "endpoint": "track_metric"}).execute()
        return {"status": "tracked", "metric_name": metric_name, "value": value_float, "dimension": dimension, "system": "KRONYX_OBSERVATORY"}
    except Exception as e:
        return {"status": "error", "message": "metric tracking failed", "system": "KRONYX_OBSERVATORY"}


def observatory_get_dashboard(api_key, db, ai_id=None):
    try:
        q = db.table("observatory_metrics").select("*").eq("api_key", api_key)
        if ai_id:
            ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
            q = q.eq("ai_id", ai_id_clean)
        result = q.order("created_at", desc=True).limit(500).execute()
        rows = result.data or []
        by_metric = {}
        for r in rows:
            name = r.get("metric_name", "unknown")
            val = r.get("value", 0)
            if name not in by_metric:
                by_metric[name] = {"values": [], "dimension": r.get("dimension", "performance"), "unit": r.get("unit", "")}
            by_metric[name]["values"].append(val)
        summary = {}
        for name, data in by_metric.items():
            vals = data["values"]
            summary[name] = {"current": vals[0] if vals else 0, "average": round(sum(vals) / len(vals), 3) if vals else 0, "min": min(vals) if vals else 0, "max": max(vals) if vals else 0, "count": len(vals), "dimension": data["dimension"], "unit": data["unit"]}
        today_str = str(date.today())
        today_count = db.table("observatory_metrics").select("id", count="exact").eq("api_key", api_key).gte("created_at", today_str).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OBSERVATORY", "endpoint": "get_dashboard"}).execute()
        return {"status": "success", "metrics_today": today_count.count or 0, "total_metrics_tracked": len(rows), "metric_summary": summary, "system": "KRONYX_OBSERVATORY"}
    except Exception as e:
        return {"status": "error", "message": "get dashboard failed", "system": "KRONYX_OBSERVATORY"}


def observatory_detect_anomaly(metric_name, current_value, api_key, db, threshold_multiplier=2.0):
    try:
        if not metric_name or current_value is None:
            return {"status": "error", "message": "metric_name and current_value required", "system": "KRONYX_OBSERVATORY"}
        historical = db.table("observatory_metrics").select("value").eq("metric_name", metric_name).eq("api_key", api_key).limit(100).execute()
        hist_values = [r.get("value", 0) for r in (historical.data or []) if r.get("value") is not None]
        if len(hist_values) < 5:
            return {"status": "insufficient_data", "message": "need at least 5 data points", "system": "KRONYX_OBSERVATORY"}
        avg = sum(hist_values) / len(hist_values)
        variance = sum((v - avg) ** 2 for v in hist_values) / len(hist_values)
        std_dev = variance ** 0.5
        threshold = avg + (std_dev * threshold_multiplier)
        is_anomaly = float(current_value) > threshold or float(current_value) < (avg - std_dev * threshold_multiplier)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OBSERVATORY", "endpoint": "detect_anomaly"}).execute()
        return {"status": "analyzed", "metric_name": metric_name, "current_value": float(current_value), "historical_average": round(avg, 3), "std_dev": round(std_dev, 3), "threshold": round(threshold, 3), "is_anomaly": is_anomaly, "severity": "high" if is_anomaly and abs(float(current_value) - avg) > std_dev * 3 else "medium" if is_anomaly else "normal", "system": "KRONYX_OBSERVATORY"}
    except Exception as e:
        return {"status": "error", "message": "anomaly detection failed", "system": "KRONYX_OBSERVATORY"}


def time_machine_snapshot(ai_id, state_data, api_key, db, label=""):
    try:
        if not ai_id or not state_data:
            return {"status": "error", "message": "ai_id and state_data required", "system": "KRONYX_TIME_MACHINE"}
        if len(str(state_data)) > 10000:
            return {"status": "error", "message": "state_data too large", "system": "KRONYX_TIME_MACHINE"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        snapshot_id = hashlib.sha256(f"{ai_id_clean}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("time_machine").insert({"snapshot_id": snapshot_id, "ai_id": ai_id_clean, "api_key": api_key, "state_data": str(state_data)[:5000], "label": (label or "")[:200], "snapshot_time": datetime.utcnow().isoformat()}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TIME_MACHINE", "endpoint": "snapshot"}).execute()
        return {"status": "snapshot_saved", "snapshot_id": snapshot_id, "ai_id": ai_id_clean, "label": label or f"Snapshot {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}", "system": "KRONYX_TIME_MACHINE"}
    except Exception as e:
        return {"status": "error", "message": "snapshot failed", "system": "KRONYX_TIME_MACHINE"}


def time_machine_restore(snapshot_id, api_key, db):
    try:
        if not snapshot_id:
            return {"status": "error", "message": "snapshot_id required", "system": "KRONYX_TIME_MACHINE"}
        result = db.table("time_machine").select("*").eq("snapshot_id", snapshot_id).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "error", "message": "snapshot not found", "system": "KRONYX_TIME_MACHINE"}
        snapshot = result.data[0]
        import ast
        try:
            state = ast.literal_eval(snapshot.get("state_data", "{}"))
        except Exception:
            state = {"raw": snapshot.get("state_data", "")}
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TIME_MACHINE", "endpoint": "restore"}).execute()
        return {"status": "restored", "snapshot_id": snapshot_id, "ai_id": snapshot.get("ai_id", ""), "state": state, "snapshot_time": snapshot.get("snapshot_time", ""), "label": snapshot.get("label", ""), "system": "KRONYX_TIME_MACHINE"}
    except Exception as e:
        return {"status": "error", "message": "restore failed", "system": "KRONYX_TIME_MACHINE"}


def time_machine_get_history(ai_id, api_key, db, limit=20):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_TIME_MACHINE"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        limit = min(max(limit, 1), 100)
        result = db.table("time_machine").select("snapshot_id, ai_id, label, snapshot_time, created_at").eq("ai_id", ai_id_clean).eq("api_key", api_key).order("created_at", desc=True).limit(limit).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TIME_MACHINE", "endpoint": "get_history"}).execute()
        return {"status": "success", "ai_id": ai_id_clean, "snapshots": result.data or [], "total": len(result.data or []), "system": "KRONYX_TIME_MACHINE"}
    except Exception as e:
        return {"status": "error", "message": "get history failed", "system": "KRONYX_TIME_MACHINE"}


def conscience_check_ethics(decision, api_key, db):
    try:
        if not decision:
            return {"status": "error", "message": "decision required", "system": "KRONYX_CONSCIENCE"}
        if len(decision) > 10000:
            return {"status": "error", "message": "decision too long", "system": "KRONYX_CONSCIENCE"}
        d_lower = decision.lower()
        ethical_frameworks = {
            "harm_prevention": ["harm", "hurt", "damage", "injure", "kill", "destroy", "abuse"],
            "fairness": ["fair", "unfair", "bias", "discriminate", "equal", "unequal", "prejudice"],
            "privacy": ["private", "personal", "confidential", "secret", "expose", "leak"],
            "autonomy": ["force", "coerce", "manipulate", "deceive", "trick", "control"],
            "dignity": ["degrade", "humiliate", "shame", "insult", "disrespect", "mock"]
        }
        ethical_issues = []
        for framework, triggers in ethical_frameworks.items():
            triggered = [t for t in triggers if t in d_lower]
            if triggered:
                ethical_issues.append({"framework": framework, "triggers": triggered, "concern": f"This decision may raise {framework.replace('_', ' ')} concerns"})
        ethics_score = max(0, 100 - (len(ethical_issues) * 20))
        bias_signals = ["all users", "every user", "always", "never"]
        bias_found = [s for s in bias_signals if s in d_lower]
        if bias_found:
            ethical_issues.append({"framework": "fairness", "triggers": bias_found, "concern": "Overgeneralization detected - check for potential bias"})
            ethics_score -= 10
        ethics_score = max(0, ethics_score)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "CONSCIENCE", "endpoint": "check_ethics"}).execute()
        return {"status": "checked", "ethics_score": ethics_score, "ethical_issues": ethical_issues, "issues_found": len(ethical_issues), "recommendation": "Review ethical concerns before deployment" if ethical_issues else "No ethical concerns detected", "system": "KRONYX_CONSCIENCE"}
    except Exception as e:
        return {"status": "error", "message": "ethics check failed", "system": "KRONYX_CONSCIENCE"}
