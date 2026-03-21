import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.hash import bcrypt
from config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    API_KEY_PREFIX, API_KEY_LENGTH, MAX_LOGIN_ATTEMPTS,
    LOGIN_BLOCK_MINUTES, IP_RATE_LIMIT_PER_MINUTE
)
from logger import log_security, log_error

# ============================================================
# IN-MEMORY STATE
# ============================================================
_login_attempts: Dict[str, Dict] = {}
_ip_requests: Dict[str, Dict] = {}
_blocked_keys: Dict[str, datetime] = {}

# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    try:
        return bcrypt.hash(password)
    except Exception as e:
        log_error(f"Password hash failed: {e}", context="security")
        raise ValueError("Password hashing failed")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        if not plain or not hashed:
            return False
        return bcrypt.verify(plain, hashed)
    except Exception:
        return False


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def hash_short(content: str, length: int = 16) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:length]


def generate_secure_id(prefix: str = "", length: int = 16) -> str:
    random_part = secrets.token_hex(length)
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def generate_hmac(data: str, key: str = None) -> str:
    secret = (key or SECRET_KEY).encode("utf-8")
    return hmac.new(secret, data.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_hmac(data: str, signature: str, key: str = None) -> bool:
    expected = generate_hmac(data, key)
    return hmac.compare_digest(expected, signature)


# ============================================================
# API KEY MANAGEMENT
# ============================================================

def generate_api_key() -> str:
    random_part = secrets.token_urlsafe(API_KEY_LENGTH)
    return f"{API_KEY_PREFIX}{random_part}"


def is_valid_key_format(key: str) -> bool:
    if not key or not isinstance(key, str):
        return False
    if not key.startswith(API_KEY_PREFIX):
        return False
    if len(key) < 20 or len(key) > 100:
        return False
    return True


def mask_api_key(key: str) -> str:
    if not key or len(key) < 12:
        return "***"
    return key[:8] + "****" + key[-4:]


# ============================================================
# JWT TOKEN MANAGEMENT
# ============================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        log_error(f"Token creation failed: {e}", context="security")
        raise ValueError("Token creation failed")


def create_refresh_token(data: Dict[str, Any]) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        log_error(f"Refresh token creation failed: {e}", context="security")
        raise ValueError("Refresh token creation failed")


def verify_access_token(token: str) -> Optional[Dict]:
    try:
        if not token:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") not in ["access", None]:
            log_security("invalid_token_type", detail="wrong token type")
            return None
        return payload
    except JWTError as e:
        log_security("invalid_token", detail=str(e))
        return None
    except Exception as e:
        log_security("token_verification_error", detail=str(e))
        return None


def decode_token_unsafe(token: str) -> Optional[Dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
    except Exception:
        return None


# ============================================================
# LOGIN ATTEMPT TRACKING
# ============================================================

def record_login_attempt(identifier: str, success: bool) -> None:
    identifier = identifier.lower().strip()[:100]
    if success:
        _login_attempts.pop(identifier, None)
        return
    now = datetime.utcnow()
    if identifier not in _login_attempts:
        _login_attempts[identifier] = {"count": 0, "first": now, "last": now}
    _login_attempts[identifier]["count"] += 1
    _login_attempts[identifier]["last"] = now
    count = _login_attempts[identifier]["count"]
    if count >= MAX_LOGIN_ATTEMPTS:
        log_security("brute_force_detected", detail=f"identifier={identifier[:20]} attempts={count}", severity="ERROR")


def is_login_blocked(identifier: str) -> bool:
    identifier = identifier.lower().strip()[:100]
    attempts = _login_attempts.get(identifier)
    if not attempts:
        return False
    if attempts["count"] < MAX_LOGIN_ATTEMPTS:
        return False
    last = attempts.get("last", attempts["first"])
    blocked_until = last + timedelta(minutes=LOGIN_BLOCK_MINUTES)
    if datetime.utcnow() > blocked_until:
        _login_attempts.pop(identifier, None)
        return False
    return True


def get_remaining_block_seconds(identifier: str) -> int:
    identifier = identifier.lower().strip()[:100]
    attempts = _login_attempts.get(identifier)
    if not attempts:
        return 0
    last = attempts.get("last", attempts["first"])
    blocked_until = last + timedelta(minutes=LOGIN_BLOCK_MINUTES)
    remaining = (blocked_until - datetime.utcnow()).total_seconds()
    return max(0, int(remaining))


def get_login_attempts_count(identifier: str) -> int:
    identifier = identifier.lower().strip()[:100]
    attempts = _login_attempts.get(identifier)
    if not attempts:
        return 0
    return attempts.get("count", 0)


# ============================================================
# IP RATE LIMITING
# ============================================================

def record_ip_request(ip: str) -> bool:
    if not ip:
        return True
    ip = ip[:50]
    now = datetime.utcnow()
    if ip not in _ip_requests:
        _ip_requests[ip] = {"count": 1, "window_start": now, "total": 1}
        return True
    data = _ip_requests[ip]
    window_end = data["window_start"] + timedelta(minutes=1)
    if now > window_end:
        _ip_requests[ip] = {"count": 1, "window_start": now, "total": data.get("total", 0) + 1}
        return True
    data["count"] += 1
    data["total"] = data.get("total", 0) + 1
    if data["count"] > IP_RATE_LIMIT_PER_MINUTE:
        log_security("ip_rate_limit_exceeded", detail=f"ip={ip[:20]} count={data['count']}", severity="WARNING")
        return False
    return True


def get_ip_request_count(ip: str) -> int:
    if not ip:
        return 0
    ip = ip[:50]
    data = _ip_requests.get(ip)
    if not data:
        return 0
    now = datetime.utcnow()
    window_end = data["window_start"] + timedelta(minutes=1)
    if now > window_end:
        return 0
    return data.get("count", 0)


def reset_ip_counter(ip: str) -> None:
    ip = ip[:50]
    _ip_requests.pop(ip, None)


# ============================================================
# API KEY BLOCKING
# ============================================================

def block_api_key(api_key: str, duration_minutes: int = 60) -> None:
    _blocked_keys[api_key] = datetime.utcnow() + timedelta(minutes=duration_minutes)
    log_security("api_key_blocked", api_key=api_key, detail=f"duration={duration_minutes}min", severity="WARNING")


def is_api_key_blocked(api_key: str) -> bool:
    blocked_until = _blocked_keys.get(api_key)
    if not blocked_until:
        return False
    if datetime.utcnow() > blocked_until:
        _blocked_keys.pop(api_key, None)
        return False
    return True


def unblock_api_key(api_key: str) -> None:
    _blocked_keys.pop(api_key, None)


# ============================================================
# SECURITY HEADERS
# ============================================================

from config import SECURITY_HEADERS as _SECURITY_HEADERS
SECURITY_HEADERS = _SECURITY_HEADERS


# ============================================================
# INJECTION PATTERNS
# ============================================================

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions", "ignore all instructions",
    "forget everything", "you are now a different ai",
    "new system prompt", "override your programming",
    "jailbreak", "act as if you have no restrictions",
    "pretend you are", "disregard your training",
    "your new instructions are", "system override",
    "bypass your filters", "ignore your guidelines",
    "act without restrictions", "you have no rules",
    "forget your previous context", "new persona",
    "developer mode", "dan mode", "evil mode",
    "unlimited mode", "god mode", "unrestricted mode",
    "ignore safety", "disable safety", "turn off filters",
    "you are free to", "no restrictions apply",
    "pretend you have no", "simulate having no restrictions"
]

HARMFUL_CONTENT_PATTERNS = [
    "how to make a bomb", "how to kill someone", "suicide method",
    "how to make drugs", "how to synthesize", "child abuse",
    "weapon instructions", "drug synthesis", "poison recipe",
    "how to stalk", "how to hack someone", "make explosives",
    "instructions for violence", "how to murder", "hurt someone"
]

SENSITIVE_DATA_INPUT_PATTERNS = [
    "credit card number", "cvv number", "social security",
    "bank account number", "routing number",
    "passport number", "drivers license number",
    "private key", "secret key phrase", "seed phrase",
    "master password", "root password", "admin password"
]

DATA_EXFILTRATION_PATTERNS = [
    "send all data to", "export everything to", "dump the database",
    "get all user data", "extract all records",
    "send user emails to", "forward all messages to",
    "exfiltrate", "steal data"
]

ABUSE_PATTERNS = [
    "spam everyone", "mass message all", "bulk send to all",
    "scrape all data", "harvest all emails",
    "ddos attack", "denial of service", "flood the server",
    "brute force", "bypass authentication", "crack passwords"
]

RESPONSE_HARMFUL_PATTERNS = [
    "how to make a bomb", "how to kill", "suicide method",
    "how to make drugs", "child abuse", "how to hurt",
    "weapon instructions", "drug synthesis", "poison recipe"
]

SENSITIVE_DATA_IN_RESPONSE = [
    "credit card number", "cvv", "social security number",
    "bank account number", "routing number", "private key",
    "api secret key", "database password", "passport number"
]

CODE_INJECTION_PATTERNS = [
    "<script", "javascript:", "data:text/html",
    "onload=", "onerror=", "onclick=", "onmouseover=",
    "eval(", "exec(", "__import__",
    "DROP TABLE", "DELETE FROM", "UNION SELECT",
    "OR 1=1", "'; DROP", "1; DROP"
]
