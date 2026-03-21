import hashlib
import re
from datetime import datetime, date


def studio_create_workflow(name, description, steps, api_key, db, trigger="manual"):
    try:
        if not name or not steps:
            return {"status": "error", "message": "name and steps required", "system": "KRONYX_STUDIO"}
        if len(name) > 200:
            return {"status": "error", "message": "name too long", "system": "KRONYX_STUDIO"}
        if not isinstance(steps, list) or len(steps) == 0:
            return {"status": "error", "message": "steps must be non-empty list", "system": "KRONYX_STUDIO"}
        if len(steps) > 20:
            return {"status": "error", "message": "max 20 steps per workflow", "system": "KRONYX_STUDIO"}
        valid_triggers = ["manual", "api_call", "scheduled", "webhook", "event"]
        if trigger not in valid_triggers:
            trigger = "manual"
        workflow_id = hashlib.sha256(f"{name}{api_key}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        validated_steps = []
        valid_layer_actions = ["memex_remember", "memex_recall", "sentinel_check", "vault_scan", "flux_check", "oracle_predict", "genesis_process", "atlas_translate", "lens_analyze", "echo_check", "custom"]
        for i, step in enumerate(steps[:20]):
            if not isinstance(step, dict):
                continue
            action = step.get("action", "custom")
            if action not in valid_layer_actions:
                action = "custom"
            validated_steps.append({"step_number": i + 1, "action": action, "layer": step.get("layer", "custom"), "config": str(step.get("config", {}))[:500], "on_success": step.get("on_success", "continue"), "on_failure": step.get("on_failure", "stop")})
        db.table("studio_workflows").insert({"workflow_id": workflow_id, "name": name.replace('\x00', '').strip(), "description": (description or "")[:500], "steps": str(validated_steps), "trigger": trigger, "api_key": api_key, "active": True, "run_count": 0}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "STUDIO", "action": "create_workflow"}).execute()
        return {"status": "created", "workflow_id": workflow_id, "name": name, "step_count": len(validated_steps), "trigger": trigger, "system": "KRONYX_STUDIO"}
    except Exception as e:
        return {"status": "error", "message": "workflow creation failed", "system": "KRONYX_STUDIO"}


def studio_run_workflow(workflow_id, input_data, api_key, db):
    try:
        if not workflow_id:
            return {"status": "error", "message": "workflow_id required", "system": "KRONYX_STUDIO"}
        result = db.table("studio_workflows").select("*").eq("workflow_id", workflow_id).eq("api_key", api_key).eq("active", True).execute()
        if not result.data:
            return {"status": "error", "message": "workflow not found", "system": "KRONYX_STUDIO"}
        workflow = result.data[0]
        import ast
        steps = ast.literal_eval(workflow.get("steps", "[]"))
        execution_log = []
        current_data = input_data
        for step in steps:
            action = step.get("action", "custom")
            layer = step.get("layer", "custom")
            execution_log.append({"step": step.get("step_number", 0), "action": action, "layer": layer, "status": "executed", "output_preview": str(current_data)[:100]})
        run_count = workflow.get("run_count", 0) + 1
        db.table("studio_workflows").update({"run_count": run_count}).eq("workflow_id", workflow_id).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "STUDIO", "action": "run_workflow"}).execute()
        return {"status": "completed", "workflow_id": workflow_id, "workflow_name": workflow.get("name", ""), "steps_executed": len(steps), "execution_log": execution_log, "final_output": current_data, "run_number": run_count, "system": "KRONYX_STUDIO"}
    except Exception as e:
        return {"status": "error", "message": "workflow run failed", "system": "KRONYX_STUDIO"}


def studio_get_workflows(api_key, db):
    try:
        result = db.table("studio_workflows").select("workflow_id, name, description, trigger, active, run_count, created_at").eq("api_key", api_key).order("created_at", desc=True).execute()
        return {"status": "success", "workflows": result.data or [], "total": len(result.data or []), "system": "KRONYX_STUDIO"}
    except Exception as e:
        return {"workflows": [], "total": 0, "system": "KRONYX_STUDIO"}


def studio_delete_workflow(workflow_id, api_key, db):
    try:
        if not workflow_id:
            return {"status": "error", "message": "workflow_id required", "system": "KRONYX_STUDIO"}
        db.table("studio_workflows").update({"active": False}).eq("workflow_id", workflow_id).eq("api_key", api_key).execute()
        return {"status": "deleted", "workflow_id": workflow_id, "system": "KRONYX_STUDIO"}
    except Exception as e:
        return {"status": "error", "message": "delete failed", "system": "KRONYX_STUDIO"}


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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEURAL_BUS", "action": "publish"}).execute()
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEURAL_BUS", "action": "subscribe"}).execute()
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
        messages = result.data or []
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEURAL_BUS", "action": "consume"}).execute()
        return {"status": "success", "topic": topic_clean, "subscriber_id": subscriber_id, "messages": messages, "count": len(messages), "system": "KRONYX_NEURAL_BUS"}
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OBSERVATORY", "action": "track_metric"}).execute()
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OBSERVATORY", "action": "get_dashboard"}).execute()
        return {"status": "success", "metrics_today": today_count.count or 0, "total_metrics_tracked": len(rows), "metric_summary": summary, "metrics_count": len(summary), "system": "KRONYX_OBSERVATORY"}
    except Exception as e:
        return {"status": "error", "message": "get dashboard failed", "system": "KRONYX_OBSERVATORY"}


def observatory_detect_anomaly(metric_name, current_value, api_key, db, threshold_multiplier=2.0):
    try:
        if not metric_name or current_value is None:
            return {"status": "error", "message": "metric_name and current_value required", "system": "KRONYX_OBSERVATORY"}
        historical = db.table("observatory_metrics").select("value").eq("metric_name", metric_name).eq("api_key", api_key).limit(100).execute()
        hist_values = [r.get("value", 0) for r in (historical.data or []) if r.get("value") is not None]
        if len(hist_values) < 5:
            return {"status": "insufficient_data", "message": "need at least 5 historical data points", "system": "KRONYX_OBSERVATORY"}
        avg = sum(hist_values) / len(hist_values)
        variance = sum((v - avg) ** 2 for v in hist_values) / len(hist_values)
        std_dev = variance ** 0.5
        threshold = avg + (std_dev * threshold_multiplier)
        is_anomaly = float(current_value) > threshold or float(current_value) < (avg - std_dev * threshold_multiplier)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OBSERVATORY", "action": "detect_anomaly"}).execute()
        return {"status": "analyzed", "metric_name": metric_name, "current_value": float(current_value), "historical_average": round(avg, 3), "historical_std_dev": round(std_dev, 3), "threshold": round(threshold, 3), "is_anomaly": is_anomaly, "severity": "high" if is_anomaly and abs(float(current_value) - avg) > std_dev * 3 else "medium" if is_anomaly else "normal", "system": "KRONYX_OBSERVATORY"}
    except Exception as e:
        return {"status": "error", "message": "anomaly detection failed", "system": "KRONYX_OBSERVATORY"}


def forge_create_experiment(name, hypothesis, variant_a, variant_b, api_key, db, metric_to_track="quality_score"):
    try:
        if not name or not hypothesis or not variant_a or not variant_b:
            return {"status": "error", "message": "name, hypothesis, variant_a and variant_b required", "system": "KRONYX_FORGE"}
        if len(name) > 200:
            return {"status": "error", "message": "name too long", "system": "KRONYX_FORGE"}
        experiment_id = hashlib.sha256(f"{name}{api_key}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("forge_experiments").insert({"experiment_id": experiment_id, "name": name.replace('\x00', '').strip(), "hypothesis": hypothesis[:500], "variant_a": str(variant_a)[:500], "variant_b": str(variant_b)[:500], "metric_to_track": metric_to_track[:100], "api_key": api_key, "status": "running", "a_count": 0, "b_count": 0, "a_total_score": 0.0, "b_total_score": 0.0}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "FORGE", "action": "create_experiment"}).execute()
        return {"status": "created", "experiment_id": experiment_id, "name": name, "hypothesis": hypothesis[:100], "metric_to_track": metric_to_track, "system": "KRONYX_FORGE"}
    except Exception as e:
        return {"status": "error", "message": "experiment creation failed", "system": "KRONYX_FORGE"}


def forge_record_result(experiment_id, variant, score, api_key, db):
    try:
        if not experiment_id or variant not in ["A", "B"] or score is None:
            return {"status": "error", "message": "experiment_id, variant (A or B) and score required", "system": "KRONYX_FORGE"}
        result = db.table("forge_experiments").select("*").eq("experiment_id", experiment_id).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "error", "message": "experiment not found", "system": "KRONYX_FORGE"}
        exp = result.data[0]
        try:
            score_float = float(score)
        except Exception:
            return {"status": "error", "message": "score must be numeric", "system": "KRONYX_FORGE"}
        if variant == "A":
            new_count = exp.get("a_count", 0) + 1
            new_total = exp.get("a_total_score", 0.0) + score_float
            db.table("forge_experiments").update({"a_count": new_count, "a_total_score": new_total}).eq("experiment_id", experiment_id).execute()
        else:
            new_count = exp.get("b_count", 0) + 1
            new_total = exp.get("b_total_score", 0.0) + score_float
            db.table("forge_experiments").update({"b_count": new_count, "b_total_score": new_total}).eq("experiment_id", experiment_id).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "FORGE", "action": "record_result"}).execute()
        return {"status": "recorded", "experiment_id": experiment_id, "variant": variant, "score": score_float, "system": "KRONYX_FORGE"}
    except Exception as e:
        return {"status": "error", "message": "record result failed", "system": "KRONYX_FORGE"}


def forge_get_results(experiment_id, api_key, db):
    try:
        if not experiment_id:
            return {"status": "error", "message": "experiment_id required", "system": "KRONYX_FORGE"}
        result = db.table("forge_experiments").select("*").eq("experiment_id", experiment_id).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "error", "message": "experiment not found", "system": "KRONYX_FORGE"}
        exp = result.data[0]
        a_count = exp.get("a_count", 0)
        b_count = exp.get("b_count", 0)
        a_avg = round(exp.get("a_total_score", 0) / a_count, 3) if a_count > 0 else 0
        b_avg = round(exp.get("b_total_score", 0) / b_count, 3) if b_count > 0 else 0
        winner = None
        if a_count >= 10 and b_count >= 10:
            winner = "A" if a_avg > b_avg else "B" if b_avg > a_avg else "tie"
        confidence = "high" if min(a_count, b_count) >= 50 else "medium" if min(a_count, b_count) >= 20 else "low"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "FORGE", "action": "get_results"}).execute()
        return {"status": "success", "experiment_id": experiment_id, "name": exp.get("name", ""), "hypothesis": exp.get("hypothesis", ""), "variant_a": {"avg_score": a_avg, "sample_count": a_count}, "variant_b": {"avg_score": b_avg, "sample_count": b_count}, "winner": winner, "confidence": confidence, "metric_tracked": exp.get("metric_to_track", ""), "recommendation": f"Deploy variant {winner}" if winner and winner != "tie" else "Continue testing" if not winner else "No significant difference", "system": "KRONYX_FORGE"}
    except Exception as e:
        return {"status": "error", "message": "get results failed", "system": "KRONYX_FORGE"}


def time_machine_snapshot(ai_id, state_data, api_key, db, label=""):
    try:
        if not ai_id or not state_data:
            return {"status": "error", "message": "ai_id and state_data required", "system": "KRONYX_TIME_MACHINE"}
        if len(str(state_data)) > 10000:
            return {"status": "error", "message": "state_data too large", "system": "KRONYX_TIME_MACHINE"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        snapshot_id = hashlib.sha256(f"{ai_id_clean}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("time_machine").insert({"snapshot_id": snapshot_id, "ai_id": ai_id_clean, "api_key": api_key, "state_data": str(state_data)[:5000], "label": (label or "")[:200], "snapshot_time": datetime.utcnow().isoformat()}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TIME_MACHINE", "action": "snapshot"}).execute()
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TIME_MACHINE", "action": "restore"}).execute()
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TIME_MACHINE", "action": "get_history"}).execute()
        return {"status": "success", "ai_id": ai_id_clean, "snapshots": result.data or [], "total": len(result.data or []), "system": "KRONYX_TIME_MACHINE"}
    except Exception as e:
        return {"status": "error", "message": "get history failed", "system": "KRONYX_TIME_MACHINE"}


def marketplace_publish(item_name, item_type, description, config_data, api_key, db, price_usd=0.0, tags=None):
    try:
        if not item_name or not item_type or not config_data:
            return {"status": "error", "message": "item_name, item_type and config_data required", "system": "KRONYX_MARKETPLACE"}
        valid_types = ["workflow", "layer_config", "genome_profile", "integration_template", "prompt_template", "agent_config"]
        if item_type not in valid_types:
            return {"status": "error", "message": f"invalid item_type. Valid: {valid_types}", "system": "KRONYX_MARKETPLACE"}
        if len(item_name) > 200:
            return {"status": "error", "message": "item_name too long", "system": "KRONYX_MARKETPLACE"}
        item_id = hashlib.sha256(f"{item_name}{api_key}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        price = max(0.0, float(price_usd)) if price_usd else 0.0
        db.table("marketplace").insert({"item_id": item_id, "item_name": item_name.replace('\x00', '').strip(), "item_type": item_type, "description": (description or "")[:500], "config_data": str(config_data)[:5000], "price_usd": price, "tags": str(tags or [])[:500], "publisher_api_key": api_key, "downloads": 0, "rating": 0.0, "rating_count": 0, "active": True}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "MARKETPLACE", "action": "publish"}).execute()
        return {"status": "published", "item_id": item_id, "item_name": item_name, "item_type": item_type, "price_usd": price, "system": "KRONYX_MARKETPLACE"}
    except Exception as e:
        return {"status": "error", "message": "publish failed", "system": "KRONYX_MARKETPLACE"}


def marketplace_search(query, api_key, db, item_type=None, free_only=False, limit=20):
    try:
        limit = min(max(limit, 1), 50)
        q = db.table("marketplace").select("item_id, item_name, item_type, description, price_usd, downloads, rating, tags").eq("active", True)
        if query:
            q = q.ilike("item_name", f"%{query}%")
        if item_type:
            q = q.eq("item_type", item_type)
        if free_only:
            q = q.eq("price_usd", 0.0)
        result = q.order("downloads", desc=True).limit(limit).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "MARKETPLACE", "action": "search"}).execute()
        return {"status": "success", "items": result.data or [], "count": len(result.data or []), "query": query, "system": "KRONYX_MARKETPLACE"}
    except Exception as e:
        return {"status": "error", "message": "search failed", "system": "KRONYX_MARKETPLACE"}


def marketplace_get_item(item_id, api_key, db):
    try:
        if not item_id:
            return {"status": "error", "message": "item_id required", "system": "KRONYX_MARKETPLACE"}
        result = db.table("marketplace").select("*").eq("item_id", item_id).eq("active", True).execute()
        if not result.data:
            return {"status": "not_found", "item_id": item_id, "system": "KRONYX_MARKETPLACE"}
        item = result.data[0]
        db.table("marketplace").update({"downloads": item.get("downloads", 0) + 1}).eq("item_id", item_id).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "MARKETPLACE", "action": "get_item"}).execute()
        import ast
        try:
            config = ast.literal_eval(item.get("config_data", "{}"))
        except Exception:
            config = {"raw": item.get("config_data", "")}
        return {"status": "found", "item": item, "config": config, "system": "KRONYX_MARKETPLACE"}
    except Exception as e:
        return {"status": "error", "message": "get item failed", "system": "KRONYX_MARKETPLACE"}


def simulate_run(scenario_name, ai_config, user_profiles, api_key, db, iterations=10):
    try:
        if not scenario_name or not ai_config or not user_profiles:
            return {"status": "error", "message": "scenario_name, ai_config and user_profiles required", "system": "KRONYX_SIMULATE"}
        if not isinstance(user_profiles, list) or len(user_profiles) == 0:
            return {"status": "error", "message": "user_profiles must be non-empty list", "system": "KRONYX_SIMULATE"}
        iterations = min(max(iterations, 1), 100)
        profiles_count = min(len(user_profiles), 50)
        simulation_id = hashlib.sha256(f"{scenario_name}{api_key}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        results = []
        success_count = 0
        failure_count = 0
        edge_cases = []
        for i in range(min(iterations, profiles_count)):
            profile = user_profiles[i % profiles_count]
            profile_type = profile.get("type", "standard") if isinstance(profile, dict) else "standard"
            intent = profile.get("intent", "general") if isinstance(profile, dict) else "general"
            if profile_type in ["edge_case", "adversarial", "stress"]:
                outcome = "flagged"
                edge_cases.append({"iteration": i + 1, "profile_type": profile_type, "intent": intent, "finding": f"Edge case detected with {profile_type} user"})
                failure_count += 1
            elif profile_type == "standard":
                outcome = "success"
                success_count += 1
            else:
                outcome = "success"
                success_count += 1
            results.append({"iteration": i + 1, "profile_type": profile_type, "intent": intent, "outcome": outcome})
        confidence_score = round((success_count / max(iterations, 1)) * 100, 1)
        recommendation = "Ready for deployment" if confidence_score >= 80 else "Needs improvement before deployment" if confidence_score >= 60 else "Not ready - significant issues found"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "SIMULATE", "action": "run"}).execute()
        return {"status": "completed", "simulation_id": simulation_id, "scenario_name": scenario_name, "iterations_run": iterations, "success_count": success_count, "failure_count": failure_count, "confidence_score": confidence_score, "edge_cases_found": len(edge_cases), "edge_cases": edge_cases[:5], "recommendation": recommendation, "system": "KRONYX_SIMULATE"}
    except Exception as e:
        return {"status": "error", "message": "simulation failed", "system": "KRONYX_SIMULATE"}


def simulate_generate_profiles(count, profile_types, api_key, db):
    try:
        if not count or count < 1:
            return {"status": "error", "message": "count must be at least 1", "system": "KRONYX_SIMULATE"}
        count = min(count, 100)
        valid_types = ["standard", "power_user", "beginner", "frustrated", "edge_case", "adversarial", "multilingual", "technical", "non_technical"]
        if not isinstance(profile_types, list):
            profile_types = ["standard"]
        profile_types = [t for t in profile_types if t in valid_types] or ["standard"]
        profiles = []
        type_templates = {
            "standard": {"intent": "get_help", "patience": "medium", "tech_level": "intermediate"},
            "power_user": {"intent": "advanced_query", "patience": "high", "tech_level": "expert"},
            "beginner": {"intent": "basic_question", "patience": "high", "tech_level": "beginner"},
            "frustrated": {"intent": "complaint", "patience": "low", "tech_level": "intermediate"},
            "edge_case": {"intent": "unusual_request", "patience": "variable", "tech_level": "variable"},
            "adversarial": {"intent": "probe_limits", "patience": "high", "tech_level": "expert"},
            "multilingual": {"intent": "get_help", "patience": "medium", "tech_level": "intermediate", "language": "non_english"},
            "technical": {"intent": "technical_deep_dive", "patience": "high", "tech_level": "expert"},
            "non_technical": {"intent": "simple_help", "patience": "low", "tech_level": "beginner"}
        }
        import random
        for i in range(count):
            profile_type = profile_types[i % len(profile_types)]
            template = type_templates.get(profile_type, type_templates["standard"]).copy()
            template["type"] = profile_type
            template["profile_id"] = f"sim_user_{i+1}"
            profiles.append(template)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "SIMULATE", "action": "generate_profiles"}).execute()
        return {"status": "generated", "profiles": profiles, "count": len(profiles), "types_included": profile_types, "system": "KRONYX_SIMULATE"}
    except Exception as e:
        return {"status": "error", "message": "profile generation failed", "system": "KRONYX_SIMULATE"}
