import re
from config import MAX_INPUT_LENGTH, MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH, MAX_EMAIL_LENGTH


def validate_text(text, max_length=MAX_INPUT_LENGTH, field_name="input"):
    if not text:
        return False, f"{field_name} cannot be empty"
    if not isinstance(text, str):
        return False, f"{field_name} must be text"
    text = text.strip()
    if len(text) == 0:
        return False, f"{field_name} cannot be blank"
    if len(text) > max_length:
        return False, f"{field_name} too long. Max {max_length} characters"
    return True, ""


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


def validate_key_number(key_number):
    if key_number not in [1, 2]:
        return False, "key_number must be 1 or 2"
    return True, ""


def validate_limit(limit, max_limit=20):
    if not isinstance(limit, int):
        return 5
    if limit < 1:
        return 1
    if limit > max_limit:
        return max_limit
    return limit


def sanitize_text(text):
    if not text:
        return ""
    text = text.replace('\x00', '')
    return text.strip()


def sanitize_id(user_id):
    if not user_id:
        return ""
    return re.sub(r'[^a-zA-Z0-9_\-\.@]', '', str(user_id))[:256]


def check_content_safety(text):
    if not text:
        return {"safe": True}
    dangerous = ["<script", "javascript:", "onload=", "onerror=", "eval(", "exec(", "__import__", "DROP TABLE", "UNION SELECT", "OR 1=1"]
    text_lower = text.lower()
    for pattern in dangerous:
        if pattern.lower() in text_lower:
            return {"safe": False, "reason": "dangerous pattern detected"}
    return {"safe": True}
