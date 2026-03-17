from database import analytics_log, analytics_get_stats, analytics_get_unique_users, analytics_get_peak_hours, usage_log, usage_count_total, usage_count_today, usage_by_layer, usage_get_timeline, interaction_get_by_user
from validators import validate_text, validate_user_id, sanitize_text
from logger import log_layer


def track(question, response, user_id, api_key, response_time=0.0):
    log_layer("insight", "track", api_key)
    if not question or not user_id:
        return {"status": "error", "message": "question and user_id required", "layer": "INSIGHT"}
    valid, err = validate_text(question, field_name="question")
    if not valid:
        return {"status": "error", "message": err, "layer": "INSIGHT"}
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "INSIGHT"}
    usage_log(api_key, "insight", "track")
    analytics_log(api_key, sanitize_text(user_id), sanitize_text(question), len(response), response_time)
    return {"status": "tracked", "layer": "INSIGHT"}


def get_stats(api_key):
    log_layer("insight", "stats", api_key)
    usage_log(api_key, "insight", "stats")
    stats = analytics_get_stats(api_key)
    questions = stats.get("questions", [])
    freq = {}
    for q in questions:
        key = q[:60].lower().strip() if q else ""
        if key:
            freq[key] = freq.get(key, 0) + 1
    top_questions = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    layer_usage = usage_by_layer(api_key)
    unique_users = analytics_get_unique_users(api_key)
    peak_hours = analytics_get_peak_hours(api_key)
    return {
        "total_tracked": stats.get("total_tracked", 0),
        "total_api_calls": usage_count_total(api_key),
        "calls_today": usage_count_today(api_key),
        "avg_response_time_ms": stats.get("avg_response_time", 0),
        "unique_users": unique_users,
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "usage_by_layer": layer_usage,
        "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
        "layer": "INSIGHT"
    }


def get_user_stats(api_key, user_id):
    log_layer("insight", "user_stats", api_key)
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "INSIGHT"}
    interactions = interaction_get_by_user(api_key, user_id)
    return {"user_id": user_id, "total_interactions": len(interactions), "recent_interactions": interactions[:10], "layer": "INSIGHT"}


def get_dashboard_data(api_key):
    stats = get_stats(api_key)
    return {
        "summary": {"total_calls": stats["total_api_calls"], "calls_today": stats["calls_today"], "total_tracked": stats["total_tracked"], "unique_users": stats["unique_users"]},
        "top_questions": stats["top_questions"],
        "layer_breakdown": stats["usage_by_layer"],
        "peak_hours": stats["peak_hours"],
        "layer": "INSIGHT"
    }


def get_usage_timeline(api_key, days=30):
    log_layer("insight", "timeline", api_key)
    usage_log(api_key, "insight", "timeline")
    timeline = usage_get_timeline(api_key, days)
    return {"timeline": timeline, "days": days, "layer": "INSIGHT"}


def get_layer_performance(api_key):
    log_layer("insight", "layer_performance", api_key)
    layer_usage = usage_by_layer(api_key)
    total_calls = usage_count_total(api_key)
    performance = []
    for item in layer_usage:
        layer = item.get("layer", "")
        count = item.get("count", 0)
        percentage = round((count / total_calls) * 100, 1) if total_calls > 0 else 0
        performance.append({"layer": layer, "calls": count, "percentage": percentage})
    return {"layer_performance": performance, "total_calls": total_calls, "layer": "INSIGHT"}


def get_growth_metrics(api_key):
    log_layer("insight", "growth", api_key)
    timeline = usage_get_timeline(api_key, 30)
    if len(timeline) < 2:
        return {"growth_rate": 0, "trend": "insufficient_data", "layer": "INSIGHT"}
    recent_week = sum(item["count"] for item in timeline[-7:])
    prev_week = sum(item["count"] for item in timeline[-14:-7]) if len(timeline) >= 14 else 0
    if prev_week > 0:
        growth_rate = round(((recent_week - prev_week) / prev_week) * 100, 1)
    else:
        growth_rate = 100 if recent_week > 0 else 0
    trend = "growing" if growth_rate > 5 else "declining" if growth_rate < -5 else "stable"
    return {"growth_rate_percent": growth_rate, "trend": trend, "recent_week_calls": recent_week, "previous_week_calls": prev_week, "layer": "INSIGHT"}


def get_ai_performance_summary(api_key):
    log_layer("insight", "ai_performance", api_key)
    from database import evolve_get_performance
    evolve_data = evolve_get_performance(api_key)
    stats = analytics_get_stats(api_key)
    return {
        "ai_quality_score": evolve_data.get("average_score", 0),
        "quality_trend": evolve_data.get("trend", "no_data"),
        "total_responses_tracked": evolve_data.get("total_tracked", 0),
        "avg_response_time_ms": stats.get("avg_response_time", 0),
        "total_interactions": stats.get("total_tracked", 0),
        "layer": "INSIGHT"
    }


def export_analytics(api_key):
    log_layer("insight", "export", api_key)
    full_stats = get_stats(api_key)
    timeline = get_usage_timeline(api_key, 90)
    growth = get_growth_metrics(api_key)
    return {
        "stats": full_stats,
        "timeline": timeline,
        "growth_metrics": growth,
        "exported_at": __import__("datetime").datetime.utcnow().isoformat(),
        "layer": "INSIGHT"
    }
