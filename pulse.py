import time
from database import incident_log, incident_resolve, incident_get_all, incident_count_unresolved, db, usage_log
from validators import validate_text
from logger import log_layer, log_error


def health_check():
    start = time.time()
    try:
        db.table("users").select("id").limit(1).execute()
        response_ms = round((time.time() - start) * 1000, 2)
        status = "healthy"
        if response_ms > 2000:
            status = "degraded"
        elif response_ms > 5000:
            status = "unhealthy"
        return {"status": status, "database": "connected", "response_ms": response_ms, "layer": "PULSE"}
    except Exception as e:
        log_error(str(e), context="pulse.health_check")
        return {"status": "unhealthy", "database": "disconnected", "response_ms": -1, "error": "database unreachable", "layer": "PULSE"}


def report_incident(api_key, description, severity="medium"):
    log_layer("pulse", "report_incident", api_key)
    valid, err = validate_text(description, field_name="description")
    if not valid:
        return {"status": "error", "message": err, "layer": "PULSE"}
    valid_severities = ["low", "medium", "high", "critical"]
    if severity not in valid_severities:
        severity = "medium"
    usage_log(api_key, "pulse", "incident")
    result = incident_log(api_key, f"[{severity.upper()}] {description}")
    if "error" in result:
        return {"status": "error", "message": "failed to log incident", "layer": "PULSE"}
    return {"status": "logged", "id": result.get("id", ""), "severity": severity, "description": description, "layer": "PULSE"}


def resolve_incident(incident_id, api_key):
    log_layer("pulse", "resolve", api_key)
    if not incident_id:
        return {"status": "error", "message": "incident_id required", "layer": "PULSE"}
    incident_resolve(incident_id)
    usage_log(api_key, "pulse", "resolve")
    return {"status": "resolved", "id": incident_id, "layer": "PULSE"}


def get_health_report(api_key):
    log_layer("pulse", "report", api_key)
    usage_log(api_key, "pulse", "report")
    health = health_check()
    incidents = incident_get_all(api_key)
    resolved = sum(1 for i in incidents if i.get("recovered"))
    unresolved = len(incidents) - resolved
    uptime_score = max(0, 100 - (unresolved * 10))
    status = "excellent" if uptime_score >= 90 else "good" if uptime_score >= 70 else "needs_attention"
    return {
        "current_health": health,
        "uptime_score": uptime_score,
        "total_incidents": len(incidents),
        "resolved": resolved,
        "unresolved": unresolved,
        "recent_incidents": incidents[:5],
        "status": status,
        "layer": "PULSE"
    }


def get_uptime_percentage(api_key):
    incidents = incident_get_all(api_key)
    unresolved = sum(1 for i in incidents if not i.get("recovered"))
    estimated_uptime = max(95.0, 99.9 - (unresolved * 0.1))
    return {"estimated_uptime_percent": round(estimated_uptime, 2), "unresolved_incidents": unresolved, "layer": "PULSE"}


def get_incident_history(api_key, include_resolved=True):
    log_layer("pulse", "incident_history", api_key)
    incidents = incident_get_all(api_key)
    if not include_resolved:
        incidents = [i for i in incidents if not i.get("recovered")]
    by_severity = {}
    for incident in incidents:
        desc = incident.get("description", "")
        if "[CRITICAL]" in desc:
            sev = "critical"
        elif "[HIGH]" in desc:
            sev = "high"
        elif "[MEDIUM]" in desc:
            sev = "medium"
        else:
            sev = "low"
        by_severity[sev] = by_severity.get(sev, 0) + 1
    return {"incidents": incidents, "total": len(incidents), "by_severity": by_severity, "layer": "PULSE"}


def heartbeat(api_key):
    log_layer("pulse", "heartbeat", api_key)
    health = health_check()
    usage_log(api_key, "pulse", "heartbeat")
    is_alive = health.get("status") in ["healthy", "degraded"]
    return {"alive": is_alive, "timestamp": time.time(), "health": health.get("status"), "response_ms": health.get("response_ms", -1), "layer": "PULSE"}


def get_performance_metrics(api_key):
    log_layer("pulse", "metrics", api_key)
    health = health_check()
    unresolved = incident_count_unresolved(api_key)
    usage_log(api_key, "pulse", "metrics")
    performance_score = 100
    response_ms = health.get("response_ms", 0)
    if response_ms > 1000:
        performance_score -= 20
    elif response_ms > 500:
        performance_score -= 10
    if health.get("status") != "healthy":
        performance_score -= 30
    performance_score -= unresolved * 5
    performance_score = max(0, min(100, performance_score))
    grade = "A" if performance_score >= 90 else "B" if performance_score >= 80 else "C" if performance_score >= 70 else "D"
    return {"performance_score": performance_score, "grade": grade, "database_response_ms": response_ms, "unresolved_incidents": unresolved, "overall_status": health.get("status", "unknown"), "layer": "PULSE"}


def auto_recover(api_key, description="Auto recovery attempted"):
    log_layer("pulse", "auto_recover", api_key)
    health = health_check()
    if health.get("status") == "healthy":
        return {"status": "no_recovery_needed", "health": health, "layer": "PULSE"}
    incident = incident_log(api_key, f"[HIGH] System unhealthy: {health.get('error', 'unknown')} - {description}")
    recovery_health = health_check()
    if recovery_health.get("status") == "healthy":
        if incident.get("id"):
            incident_resolve(incident["id"])
        return {"status": "recovered", "previous_health": health, "current_health": recovery_health, "layer": "PULSE"}
    return {"status": "recovery_failed", "health": recovery_health, "incident_id": incident.get("id"), "layer": "PULSE"}
