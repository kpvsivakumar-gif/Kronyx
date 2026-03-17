from database import notification_save, notification_get_all, notification_mark_read, notification_count_unread
from logger import log_layer


def create_notification(api_key, notification_type, message):
    log_layer("notifications", "create", api_key)
    valid_types = [
        "security_alert", "rate_limit_warning", "health_alert",
        "memory_limit", "key_regenerated", "new_threat",
        "incident_detected", "export_ready", "welcome"
    ]
    if notification_type not in valid_types:
        return {"status": "error", "message": f"invalid type. Valid: {valid_types}"}
    success = notification_save(api_key, notification_type, message)
    if not success:
        return {"status": "error", "message": "failed to save notification"}
    return {"status": "created", "type": notification_type}


def get_notifications(api_key, unread_only=False):
    log_layer("notifications", "get", api_key)
    notifications = notification_get_all(api_key, unread_only)
    unread_count = notification_count_unread(api_key)
    return {
        "notifications": notifications,
        "total": len(notifications),
        "unread_count": unread_count
    }


def mark_as_read(notification_id, api_key):
    log_layer("notifications", "mark_read", api_key)
    success = notification_mark_read(notification_id)
    if not success:
        return {"status": "error", "message": "notification not found"}
    return {"status": "read", "id": notification_id}


def get_unread_count(api_key):
    return {"count": notification_count_unread(api_key)}


def notify_security_threat(api_key, threat_type, user_email=None):
    message = f"VAULT blocked a {threat_type} threat on your account"
    create_notification(api_key, "security_alert", message)
    if user_email:
        from email_service import send_security_alert
        send_security_alert(user_email, threat_type)


def notify_rate_limit_warning(api_key, used, limit, user_email=None):
    percent = round((used / limit) * 100)
    message = f"You have used {percent}% of your daily API limit ({used:,}/{limit:,} calls)"
    create_notification(api_key, "rate_limit_warning", message)
    if user_email and percent >= 90:
        from email_service import send_rate_limit_warning
        send_rate_limit_warning(user_email, used, limit)


def notify_health_alert(api_key, issue, user_email=None):
    message = f"PULSE detected an issue: {issue[:100]}"
    create_notification(api_key, "health_alert", message)
    if user_email:
        from email_service import send_health_alert
        send_health_alert(user_email, issue)


def notify_key_regenerated(api_key, key_number):
    message = f"API Key {key_number} was regenerated. Update your code immediately."
    create_notification(api_key, "key_regenerated", message)


def clear_all_notifications(api_key):
    notifications = notification_get_all(api_key)
    count = 0
    for n in notifications:
        if notification_mark_read(n.get("id")):
            count += 1
    return {"status": "cleared", "count": count}
