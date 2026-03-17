import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.hash import bcrypt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, API_KEY_PREFIX
from logger import log_security

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cache-Control": "no-store, no-cache, must-revalidate",
}

_login_attempts = {}
_ip_requests = {}


def hash_password(password):
    return bcrypt.hash(password)


def verify_password(plain, hashed):
    try:
        return bcrypt.verify(plain, hashed)
    except Exception:
        return False


def generate_api_key():
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_api_key(key):
    return hashlib.sha256(key.encode()).hexdigest()


def is_valid_key_format(key):
    if not key:
        return False
    if not key.startswith(API_KEY_PREFIX):
        return False
    if len(key) < 20:
        return False
    return True


def create_access_token(data, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        log_security("invalid_token", detail=str(e))
        return None


def decode_token_email(token):
    payload = verify_access_token(token)
    if payload:
        return payload.get("sub")
    return None


def record_login_attempt(identifier, success):
    if success:
        _login_attempts.pop(identifier, None)
        return
    current = _login_attempts.get(identifier, {"count": 0, "first": datetime.utcnow()})
    current["count"] += 1
    current["last"] = datetime.utcnow()
    _login_attempts[identifier] = current
    if current["count"] >= 5:
        log_security("brute_force_detected", detail=f"id={identifier[:20]}")


def is_login_blocked(identifier):
    attempts = _login_attempts.get(identifier)
    if not attempts:
        return False
    if attempts["count"] < 5:
        return False
    last = attempts.get("last", attempts["first"])
    blocked_until = last + timedelta(minutes=30)
    if datetime.utcnow() > blocked_until:
        _login_attempts.pop(identifier, None)
        return False
    return True


def get_remaining_block_time(identifier):
    attempts = _login_attempts.get(identifier)
    if not attempts:
        return 0
    last = attempts.get("last", attempts["first"])
    blocked_until = last + timedelta(minutes=30)
    remaining = (blocked_until - datetime.utcnow()).seconds
    return max(0, remaining)


def record_ip_request(ip):
    now = datetime.utcnow()
    if ip not in _ip_requests:
        _ip_requests[ip] = {"count": 1, "window_start": now}
        return True
    data = _ip_requests[ip]
    window_end = data["window_start"] + timedelta(minutes=1)
    if now > window_end:
        _ip_requests[ip] = {"count": 1, "window_start": now}
        return True
    data["count"] += 1
    if data["count"] > 500:
        log_security("ip_rate_limit", detail=f"ip={ip}")
        return False
    return True
