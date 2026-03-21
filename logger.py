import logging
import re
import sys
from config import APP_NAME, ENVIRONMENT


def mask_api_key(key):
    if not key or len(key) < 12:
        return "***"
    return key[:8] + "****" + key[-4:]


def mask_sensitive(message):
    message = str(message)
    message = re.sub(r'kr_live_[a-zA-Z0-9_-]{20,}', lambda m: mask_api_key(m.group()), message)
    message = re.sub(r'"password"\s*:\s*"[^"]*"', '"password": "***"', message)
    message = re.sub(r'eyJ[a-zA-Z0-9_-]{20,}', '***token***', message)
    message = re.sub(
        r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        lambda m: m.group(1)[:3] + "***@" + m.group(2),
        message
    )
    return message


class SecureFormatter(logging.Formatter):
    def format(self, record):
        record.msg = mask_sensitive(str(record.msg))
        if record.args:
            try:
                record.args = tuple(
                    mask_sensitive(str(a)) if isinstance(a, str) else a
                    for a in (record.args if isinstance(record.args, tuple) else (record.args,))
                )
            except Exception:
                pass
        return super().format(record)


def setup_logger(name=APP_NAME):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO if ENVIRONMENT == "production" else logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = SecureFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


log = setup_logger()


def log_request(method, path, api_key="", status=200):
    masked = mask_api_key(api_key) if api_key else "no-key"
    log.info(f"REQUEST {method} {path} key={masked} status={status}")


def log_security(event_type, api_key="", detail=""):
    masked = mask_api_key(api_key) if api_key else "no-key"
    log.warning(f"SECURITY {event_type} key={masked} {detail}")


def log_error(error, api_key="", context=""):
    masked = mask_api_key(api_key) if api_key else "no-key"
    log.error(f"ERROR key={masked} context={context} {error}")


def log_startup():
    log.info("=" * 60)
    log.info(f"KRONYX v3.0.0 Starting")
    log.info(f"Environment: {ENVIRONMENT}")
    log.info(f"5 Elite Pillars | 14 Systems | 24 Layers | 11 Elite Features")
    log.info(f"Total Capabilities: 54")
    log.info("=" * 60)
