import re
from typing import Optional
from config import (
    MAX_INPUT_LENGTH, MAX_MEMORY_CONTENT_LENGTH,
    MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH,
    MAX_EMAIL_LENGTH, MAX_MEMORIES_PER_RECALL
)


def validate_text(text, max_length=MAX_INPUT_LENGTH, field_name="input"):
    if not text:
        return False, f"{field_name} cannot be empty"
    if not isinstance(text, str):
        return False, f"{field_name} must be text"
    text = text.strip()
    if len(text) == 0:
        return False, f"{field_name} cannot be blank"
    if len(text) > max_length:
        return False, f"{field_name} too long. Max {max_length} characters allowed"
    return True, ""


def validate_memory_content(content):
    return validate_text(content, MAX_MEMORY_CONTENT_LENGTH, "memory content")


def validate_user_id(user_id):
    if not user_id:
        return False, "user_id cannot be empty"
    if len(user_id) > 256:
        return False, "user_id too long"
    if not re.match(r'^[a-zA-Z0-9_\-\.@]+$', user_id):
        return False, "user_id contains invalid characters"
    return True, ""


def validate_query(query):
    return validate_text(query, MAX_INPUT_LENGTH, "query")


def validate_email(email):
    if not email:
        return False, "email cannot be empty"
    if len(email) > MAX_EMAIL_LENGTH:
        return False, "email too long"
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "invalid email format"
    return True, ""


def validate_password(password):
    if not password:
        return False, "password cannot be empty"
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"password must be at least {MIN_PASSWORD_LENGTH} characters"
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, "password too long"
    return True, ""


def validate_api_key_format(key):
    if not key:
        return False, "API key cannot be empty"
    if not key.startswith("kr_live_"):
        return False, "invalid API key format"
    if len(key) < 20:
        return False, "invalid API key length"
    return True, ""


def validate_limit(limit, max_limit=MAX_MEMORIES_PER_RECALL):
    if not isinstance(limit, int):
        return 5
    if limit < 1:
        return 1
    if limit > max_limit:
        return max_limit
    return limit


def validate_score(score):
    if not isinstance(score, (int, float)):
        return False, "score must be a number"
    if score < 0 or score > 100:
        return False, "score must be between 0 and 100"
    return True, ""


def validate_language_code(lang):
    if not lang:
        return False, "language code cannot be empty"
    if len(lang) > 10:
        return False, "invalid language code"
    valid = [
        "en", "hi", "ar", "es", "fr", "de", "zh-cn", "zh-tw",
        "ja", "ko", "pt", "ru", "it", "nl", "pl", "tr", "vi",
        "th", "id", "ms", "bn", "te", "ta", "ur", "mr", "gu",
        "kn", "ml", "pa", "sv", "da", "fi", "no", "cs", "sk",
        "ro", "hu", "uk", "el", "he", "fa", "sw", "af", "sq",
        "hy", "az", "eu", "be", "bs", "bg", "ca", "hr", "cy",
        "et", "tl", "gl", "ka", "ht", "is", "ga", "lv", "lt",
        "mk", "mt", "sr", "si", "sl", "so", "tk", "uz", "zu", "auto"
    ]
    if lang not in valid:
        return False, f"unsupported language: {lang}"
    return True, ""


def validate_key_number(key_number):
    if key_number not in [1, 2]:
        return False, "key_number must be 1 or 2"
    return True, ""


def sanitize_text(text):
    if not text:
        return ""
    text = text.replace('\x00', '')
    return text.strip()


def sanitize_user_id(user_id):
    if not user_id:
        return ""
    return re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]


def check_content_safety(text):
    if not text:
        return {"safe": True}
    dangerous = [
        "<script", "javascript:", "data:text/html",
        "onload=", "onerror=", "onclick=",
        "eval(", "exec(", "__import__",
        "DROP TABLE", "DELETE FROM",
        "UNION SELECT", "OR 1=1",
    ]
    text_lower = text.lower()
    for pattern in dangerous:
        if pattern.lower() in text_lower:
            return {"safe": False, "reason": f"dangerous pattern detected"}
    return {"safe": True}
