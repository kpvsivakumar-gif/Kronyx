import httpx
from database import webhook_save, webhook_get_all, webhook_delete
from validators import validate_text
from logger import log_layer, log_error

VALID_EVENTS = [
    "memory.stored",
    "memory.deleted",
    "threat.detected",
    "rate_limit.reached",
    "health.incident",
    "key.regenerated",
    "user.signup",
    "sentinel.flagged",
    "vault.blocked"
]


def register_webhook(api_key, url, events):
    log_layer("webhooks", "register", api_key)
    if not url:
        return {"status": "error", "message": "url required"}
    valid, err = validate_text(url, max_length=2000, field_name="url")
    if not valid:
        return {"status": "error", "message": err}
    if not url.startswith(("http://", "https://")):
        return {"status": "error", "message": "url must start with http or https"}
    if not isinstance(events, list) or len(events) == 0:
        return {"status": "error", "message": "events must be a non-empty list"}
    invalid_events = [e for e in events if e not in VALID_EVENTS]
    if invalid_events:
        return {"status": "error", "message": f"invalid events: {invalid_events}. Valid: {VALID_EVENTS}"}
    success = webhook_save(api_key, url, events)
    if not success:
        return {"status": "error", "message": "failed to register webhook"}
    return {"status": "registered", "url": url[:50], "events": events, "valid_events": VALID_EVENTS}


def get_webhooks(api_key):
    log_layer("webhooks", "get", api_key)
    webhooks = webhook_get_all(api_key)
    return {"webhooks": webhooks, "total": len(webhooks)}


def delete_webhook(webhook_id, api_key):
    log_layer("webhooks", "delete", api_key)
    if not webhook_id:
        return {"status": "error", "message": "webhook_id required"}
    success = webhook_delete(webhook_id, api_key)
    if not success:
        return {"status": "error", "message": "webhook not found"}
    return {"status": "deleted", "id": webhook_id}


def fire_webhook(api_key, event, payload):
    log_layer("webhooks", "fire", api_key)
    webhooks = webhook_get_all(api_key)
    fired = 0
    failed = 0
    for webhook in webhooks:
        webhook_url = webhook.get("url", "")
        webhook_events_str = webhook.get("events", "[]")
        try:
            import ast
            webhook_events = ast.literal_eval(webhook_events_str)
        except Exception:
            webhook_events = []
        if event not in webhook_events:
            continue
        try:
            response = httpx.post(
                webhook_url,
                json={"event": event, "payload": payload, "source": "KRONYX"},
                timeout=5.0,
                headers={"X-KRONYX-Event": event, "Content-Type": "application/json"}
            )
            if response.status_code < 400:
                fired += 1
            else:
                failed += 1
        except Exception as e:
            log_error(str(e), api_key=api_key, context=f"webhook_fire_{event}")
            failed += 1
    return {"event": event, "fired": fired, "failed": failed}


def test_webhook(api_key, url):
    log_layer("webhooks", "test", api_key)
    if not url:
        return {"status": "error", "message": "url required"}
    try:
        response = httpx.post(
            url,
            json={"event": "webhook.test", "payload": {"message": "KRONYX webhook test successful"}, "source": "KRONYX"},
            timeout=5.0,
            headers={"X-KRONYX-Event": "webhook.test", "Content-Type": "application/json"}
        )
        return {
            "status": "success" if response.status_code < 400 else "failed",
            "http_status": response.status_code,
            "url": url[:50]
        }
    except httpx.TimeoutException:
        return {"status": "failed", "error": "timeout - url did not respond in 5 seconds"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def get_valid_events():
    return {"events": VALID_EVENTS, "total": len(VALID_EVENTS)}
