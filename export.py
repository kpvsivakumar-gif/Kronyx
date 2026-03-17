import json
from datetime import datetime
from database import export_get_all_data, memory_get_all, analytics_get_stats, threat_get_all, usage_by_layer
from logger import log_layer


def export_all_data(api_key):
    log_layer("export", "all", api_key)
    data = export_get_all_data(api_key)
    data["exported_at"] = str(datetime.utcnow())
    data["api_key_masked"] = api_key[:8] + "****" if api_key else ""
    data["version"] = "1.0.0"
    data["disclaimer"] = "KRONYX data export. Handle this data securely."
    return data


def export_memories_only(api_key):
    log_layer("export", "memories", api_key)
    memories = memory_get_all(api_key)
    return {
        "memories": memories,
        "total": len(memories),
        "exported_at": str(datetime.utcnow()),
        "note": "Memories auto-delete after 90 days from creation date"
    }


def export_analytics_only(api_key):
    log_layer("export", "analytics", api_key)
    stats = analytics_get_stats(api_key)
    usage = usage_by_layer(api_key)
    return {
        "analytics": stats,
        "usage_by_layer": usage,
        "exported_at": str(datetime.utcnow())
    }


def export_security_data(api_key):
    log_layer("export", "security", api_key)
    threats = threat_get_all(api_key)
    return {
        "threats": threats,
        "total_threats": len(threats),
        "exported_at": str(datetime.utcnow())
    }


def generate_export_json(api_key):
    data = export_all_data(api_key)
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception:
        return json.dumps({"error": "export failed", "exported_at": str(datetime.utcnow())})


def get_export_summary(api_key):
    log_layer("export", "summary", api_key)
    memories = memory_get_all(api_key)
    threats = threat_get_all(api_key)
    analytics = analytics_get_stats(api_key)
    return {
        "summary": {
            "total_memories": len(memories),
            "total_threats": len(threats),
            "total_analytics": analytics.get("total_tracked", 0)
        },
        "available_exports": [
            "all_data",
            "memories_only",
            "analytics_only",
            "security_data"
        ],
        "format": "JSON",
        "note": "Data export includes all your stored data. Handle securely."
    }


def delete_all_user_data(api_key, user_id):
    log_layer("export", "delete_user_data", api_key)
    from database import memory_delete_by_user
    success = memory_delete_by_user(user_id, api_key)
    return {
        "status": "deleted" if success else "error",
        "user_id": user_id,
        "message": "User data deleted from KRONYX memories"
    }
