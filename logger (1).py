import logging
import re
import sys
import json
import traceback
from datetime import datetime
from config import APP_NAME, APP_VERSION, ENVIRONMENT


# ============================================================
# SENSITIVE DATA MASKING
# ============================================================

def mask_api_key(key):
    if not key or not isinstance(key, str):
        return "***"
    if len(key) < 12:
        return "***"
    return key[:8] + "****" + key[-4:]


def mask_email(email):
    if not email or "@" not in email:
        return "***"
    parts = email.split("@")
    local = parts[0]
    domain = parts[1] if len(parts) > 1 else ""
    masked_local = local[:3] + "***" if len(local) > 3 else "***"
    return f"{masked_local}@{domain}"


def mask_sensitive(message):
    if not message:
        return ""
    message = str(message)
    message = re.sub(
        r'kr_live_[a-zA-Z0-9_\-]{20,}',
        lambda m: mask_api_key(m.group()),
        message
    )
    message = re.sub(r'"password"\s*:\s*"[^"]*"', '"password": "***"', message)
    message = re.sub(r"'password'\s*:\s*'[^']*'", "'password': '***'", message)
    message = re.sub(r'eyJ[a-zA-Z0-9_\-\.]{20,}', '***jwt_token***', message)
    message = re.sub(
        r'([a-zA-Z0-9._%+\-]+)@([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
        lambda m: mask_email(m.group()),
        message
    )
    message = re.sub(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', '****-****-****-****', message)
    message = re.sub(r'\b\d{3}[\-\.]?\d{2}[\-\.]?\d{4}\b', '***-**-****', message)
    return message


# ============================================================
# SECURE FORMATTER
# ============================================================

class SecureFormatter(logging.Formatter):
    def format(self, record):
        try:
            record.msg = mask_sensitive(str(record.msg))
            if record.args:
                if isinstance(record.args, tuple):
                    record.args = tuple(
                        mask_sensitive(str(a)) if isinstance(a, str) else a
                        for a in record.args
                    )
                elif isinstance(record.args, dict):
                    record.args = {
                        k: mask_sensitive(str(v)) if isinstance(v, str) else v
                        for k, v in record.args.items()
                    }
        except Exception:
            pass
        return super().format(record)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "app": APP_NAME,
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
            "message": mask_sensitive(str(record.getMessage())),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = traceback.format_exception(*record.exc_info)[-1].strip()
        return json.dumps(log_obj)


# ============================================================
# LOGGER SETUP
# ============================================================

def setup_logger(name=APP_NAME):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    level = logging.DEBUG if ENVIRONMENT != "production" else logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    if ENVIRONMENT == "production":
        formatter = SecureFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = SecureFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


log = setup_logger()


# ============================================================
# SPECIALIZED LOG FUNCTIONS
# ============================================================

def log_request(method, path, api_key="", status=200, duration_ms=0, ip=""):
    masked_key = mask_api_key(api_key) if api_key else "no-key"
    masked_ip = ip[:10] + "..." if len(ip) > 10 else ip
    log.info(f"REQUEST {method} {path} | key={masked_key} | status={status} | {duration_ms}ms | ip={masked_ip}")


def log_security(event_type, api_key="", detail="", severity="WARNING"):
    masked = mask_api_key(api_key) if api_key else "no-key"
    safe_detail = mask_sensitive(detail)
    if severity == "CRITICAL":
        log.critical(f"SECURITY [{event_type}] key={masked} | {safe_detail}")
    elif severity == "ERROR":
        log.error(f"SECURITY [{event_type}] key={masked} | {safe_detail}")
    else:
        log.warning(f"SECURITY [{event_type}] key={masked} | {safe_detail}")


def log_error(error, api_key="", context="", exc_info=False):
    masked = mask_api_key(api_key) if api_key else "no-key"
    safe_error = mask_sensitive(str(error))
    safe_context = mask_sensitive(context)
    if exc_info:
        log.error(f"ERROR key={masked} | context={safe_context} | {safe_error}", exc_info=True)
    else:
        log.error(f"ERROR key={masked} | context={safe_context} | {safe_error}")


def log_info(message, api_key="", context=""):
    masked = mask_api_key(api_key) if api_key else ""
    key_str = f"key={masked} | " if masked else ""
    ctx_str = f"context={context} | " if context else ""
    log.info(f"{key_str}{ctx_str}{mask_sensitive(message)}")


def log_debug(message, api_key="", context=""):
    if ENVIRONMENT == "production":
        return
    masked = mask_api_key(api_key) if api_key else ""
    key_str = f"key={masked} | " if masked else ""
    ctx_str = f"context={context} | " if context else ""
    log.debug(f"{key_str}{ctx_str}{mask_sensitive(message)}")


def log_warning(message, api_key="", context=""):
    masked = mask_api_key(api_key) if api_key else ""
    key_str = f"key={masked} | " if masked else ""
    ctx_str = f"context={context} | " if context else ""
    log.warning(f"{key_str}{ctx_str}{mask_sensitive(message)}")


def log_startup():
    log.info("=" * 70)
    log.info(f"  {APP_NAME} v{APP_VERSION} Starting Up")
    log.info(f"  Environment: {ENVIRONMENT}")
    log.info(f"  5 Elite Pillars | 14 Systems | 24 Layers | 11 Elite Features")
    log.info(f"  Total Capabilities: 54")
    log.info(f"  The AWS of AI Infrastructure")
    log.info("=" * 70)


def log_shutdown():
    log.info(f"{APP_NAME} shutting down gracefully")


def log_database_event(event, detail="", success=True):
    status = "OK" if success else "FAIL"
    log.info(f"DATABASE [{status}] {event} | {mask_sensitive(detail)}")


def log_rate_limit(api_key, used, limit):
    masked = mask_api_key(api_key)
    log.warning(f"RATE_LIMIT key={masked} | used={used}/{limit}")


def log_threat(api_key, threat_type, content_preview=""):
    masked = mask_api_key(api_key)
    safe_preview = mask_sensitive(content_preview[:100])
    log.warning(f"THREAT_BLOCKED key={masked} | type={threat_type} | preview={safe_preview}")


def log_new_user(email):
    safe_email = mask_email(email)
    log.info(f"NEW_USER email={safe_email}")


def log_api_key_regenerated(api_key, key_number):
    masked = mask_api_key(api_key)
    log.info(f"KEY_REGENERATED key={masked} | key_number={key_number}")
