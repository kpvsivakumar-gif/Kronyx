import re
from typing import Tuple, Any, Optional
from config import (
    MAX_INPUT_LENGTH, MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH,
    MAX_EMAIL_LENGTH, MAX_USER_ID_LENGTH, MAX_AI_ID_LENGTH,
    MAX_MEMORY_CONTENT_LENGTH, MAX_BULK_MEMORIES, MAX_RECALL_LIMIT,
    MAX_CONTENT_LENGTH
)


# ============================================================
# TEXT VALIDATION
# ============================================================

def validate_text(text: Any, max_length: int = MAX_INPUT_LENGTH, field_name: str = "input", required: bool = True) -> Tuple[bool, str]:
    if text is None or text == "":
        if required:
            return False, f"{field_name} cannot be empty"
        return True, ""
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return False, f"{field_name} must be text"
    text = text.strip()
    if len(text) == 0:
        if required:
            return False, f"{field_name} cannot be blank"
        return True, ""
    if len(text) > max_length:
        return False, f"{field_name} too long. Max {max_length} characters, got {len(text)}"
    return True, ""


def validate_text_required(text: Any, max_length: int = MAX_INPUT_LENGTH, field_name: str = "input") -> Tuple[bool, str]:
    return validate_text(text, max_length, field_name, required=True)


def validate_content(content: Any, field_name: str = "content") -> Tuple[bool, str]:
    return validate_text(content, MAX_MEMORY_CONTENT_LENGTH, field_name, required=True)


def validate_large_text(text: Any, field_name: str = "text") -> Tuple[bool, str]:
    return validate_text(text, MAX_CONTENT_LENGTH, field_name, required=True)


# ============================================================
# EMAIL VALIDATION
# ============================================================

def validate_email(email: Any) -> Tuple[bool, str]:
    if not email:
        return False, "email cannot be empty"
    if not isinstance(email, str):
        return False, "email must be a string"
    email = email.strip().lower()
    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"email too long. Max {MAX_EMAIL_LENGTH} characters"
    if len(email) < 5:
        return False, "email too short"
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "invalid email format. Must be like: user@example.com"
    if email.count("@") != 1:
        return False, "email must contain exactly one @ symbol"
    local, domain = email.rsplit("@", 1)
    if len(local) == 0:
        return False, "email local part cannot be empty"
    if len(domain) == 0:
        return False, "email domain cannot be empty"
    if "." not in domain:
        return False, "email domain must contain a dot"
    return True, ""


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password(password: Any) -> Tuple[bool, str]:
    if not password:
        return False, "password cannot be empty"
    if not isinstance(password, str):
        return False, "password must be a string"
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"password must be at least {MIN_PASSWORD_LENGTH} characters"
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"password too long. Max {MAX_PASSWORD_LENGTH} characters"
    return True, ""


def validate_password_strength(password: Any) -> Tuple[bool, str, int]:
    valid, error = validate_password(password)
    if not valid:
        return False, error, 0
    score = 0
    feedback = []
    if len(password) >= 12:
        score += 25
    elif len(password) >= 8:
        score += 10
    if re.search(r'[A-Z]', password):
        score += 25
    else:
        feedback.append("add uppercase letters")
    if re.search(r'[a-z]', password):
        score += 25
    else:
        feedback.append("add lowercase letters")
    if re.search(r'\d', password):
        score += 15
    else:
        feedback.append("add numbers")
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        score += 10
    else:
        feedback.append("add special characters")
    if feedback:
        return True, f"weak password - {', '.join(feedback)}", score
    return True, "strong password", score


# ============================================================
# API KEY VALIDATION
# ============================================================

def validate_api_key_format(key: Any) -> Tuple[bool, str]:
    if not key:
        return False, "API key cannot be empty"
    if not isinstance(key, str):
        return False, "API key must be a string"
    if not key.startswith("kr_live_"):
        return False, "invalid API key format. Must start with kr_live_"
    if len(key) < 20:
        return False, "invalid API key length"
    if len(key) > 100:
        return False, "invalid API key length"
    return True, ""


# ============================================================
# ID VALIDATION
# ============================================================

def validate_user_id(user_id: Any) -> Tuple[bool, str]:
    if not user_id:
        return False, "user_id cannot be empty"
    if not isinstance(user_id, str):
        user_id = str(user_id)
    user_id = user_id.strip()
    if len(user_id) == 0:
        return False, "user_id cannot be blank"
    if len(user_id) > MAX_USER_ID_LENGTH:
        return False, f"user_id too long. Max {MAX_USER_ID_LENGTH} characters"
    return True, ""


def validate_ai_id(ai_id: Any) -> Tuple[bool, str]:
    if not ai_id:
        return False, "ai_id cannot be empty"
    if not isinstance(ai_id, str):
        return False, "ai_id must be a string"
    ai_id = ai_id.strip()
    if len(ai_id) == 0:
        return False, "ai_id cannot be blank"
    if len(ai_id) > MAX_AI_ID_LENGTH:
        return False, f"ai_id too long. Max {MAX_AI_ID_LENGTH} characters"
    pattern = r'^[a-zA-Z0-9_\-]+$'
    if not re.match(pattern, ai_id):
        return False, "ai_id can only contain letters, numbers, hyphens and underscores"
    return True, ""


def validate_key_number(key_number: Any) -> Tuple[bool, str]:
    try:
        key_number = int(key_number)
    except Exception:
        return False, "key_number must be 1 or 2"
    if key_number not in [1, 2]:
        return False, "key_number must be 1 or 2"
    return True, ""


# ============================================================
# NUMERIC VALIDATION
# ============================================================

def validate_limit(limit: Any, max_limit: int = 20, default: int = 5) -> int:
    try:
        limit = int(limit)
    except Exception:
        return default
    if limit < 1:
        return 1
    if limit > max_limit:
        return max_limit
    return limit


def validate_score(score: Any, field_name: str = "score") -> Tuple[bool, str]:
    if score is None:
        return False, f"{field_name} cannot be empty"
    try:
        score = float(score)
    except Exception:
        return False, f"{field_name} must be a number"
    if score < 0 or score > 100:
        return False, f"{field_name} must be between 0 and 100"
    return True, ""


def validate_integer_range(value: Any, min_val: int, max_val: int, field_name: str = "value") -> Tuple[bool, str]:
    if value is None:
        return False, f"{field_name} cannot be empty"
    try:
        value = int(value)
    except Exception:
        return False, f"{field_name} must be an integer"
    if value < min_val:
        return False, f"{field_name} must be at least {min_val}"
    if value > max_val:
        return False, f"{field_name} must be at most {max_val}"
    return True, ""


def validate_float_range(value: Any, min_val: float, max_val: float, field_name: str = "value") -> Tuple[bool, str]:
    if value is None:
        return False, f"{field_name} cannot be empty"
    try:
        value = float(value)
    except Exception:
        return False, f"{field_name} must be a number"
    if value < min_val:
        return False, f"{field_name} must be at least {min_val}"
    if value > max_val:
        return False, f"{field_name} must be at most {max_val}"
    return True, ""


def validate_confidence(confidence: Any) -> Tuple[bool, str]:
    return validate_float_range(confidence, 0.0, 1.0, "actual_confidence")


# ============================================================
# LIST VALIDATION
# ============================================================

def validate_list(items: Any, field_name: str = "items", min_items: int = 1, max_items: int = 50) -> Tuple[bool, str]:
    if not isinstance(items, list):
        return False, f"{field_name} must be a list"
    if len(items) < min_items:
        return False, f"{field_name} must have at least {min_items} item(s)"
    if len(items) > max_items:
        return False, f"{field_name} must have at most {max_items} items"
    return True, ""


def validate_string_list(items: Any, field_name: str = "items", max_items: int = 50, max_item_length: int = 500) -> Tuple[bool, str]:
    valid, error = validate_list(items, field_name, 1, max_items)
    if not valid:
        return False, error
    for i, item in enumerate(items):
        if not isinstance(item, str):
            return False, f"{field_name}[{i}] must be a string"
        if len(item) > max_item_length:
            return False, f"{field_name}[{i}] too long. Max {max_item_length} characters"
    return True, ""


def validate_dict_list(items: Any, field_name: str = "items", max_items: int = 50) -> Tuple[bool, str]:
    valid, error = validate_list(items, field_name, 1, max_items)
    if not valid:
        return False, error
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"{field_name}[{i}] must be an object"
    return True, ""


# ============================================================
# DOMAIN VALIDATION
# ============================================================

def validate_domain(domain: str, valid_domains: list, field_name: str = "domain") -> Tuple[bool, str]:
    if not domain:
        return False, f"{field_name} cannot be empty"
    if domain not in valid_domains:
        return False, f"unknown {field_name}: '{domain}'. Available: {valid_domains}"
    return True, ""


def validate_language_code(lang: Any) -> Tuple[bool, str]:
    from config import SUPPORTED_LANGUAGES
    if not lang:
        return False, "language code cannot be empty"
    if not isinstance(lang, str):
        return False, "language code must be a string"
    if lang not in SUPPORTED_LANGUAGES:
        return False, f"unsupported language: '{lang}'. Call /v1/atlas-prime/atlas/languages to see all supported languages"
    return True, ""


# ============================================================
# URL VALIDATION
# ============================================================

def validate_url(url: Any) -> Tuple[bool, str]:
    if not url:
        return False, "url cannot be empty"
    if not isinstance(url, str):
        return False, "url must be a string"
    url = url.strip()
    if len(url) > 2000:
        return False, "url too long"
    if not url.startswith(("http://", "https://")):
        return False, "url must start with http:// or https://"
    return True, ""


# ============================================================
# SANITIZATION
# ============================================================

def sanitize_text(text: Any) -> str:
    if not text:
        return ""
    text = str(text)
    text = text.replace('\x00', '')
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    return text.strip()


def sanitize_user_id(user_id: Any) -> str:
    if not user_id:
        return ""
    user_id = str(user_id)
    user_id = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)
    return user_id[:MAX_USER_ID_LENGTH]


def sanitize_ai_id(ai_id: Any) -> str:
    if not ai_id:
        return ""
    ai_id = str(ai_id)
    ai_id = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)
    return ai_id[:MAX_AI_ID_LENGTH]


def sanitize_topic(topic: Any) -> str:
    if not topic:
        return ""
    topic = str(topic)
    topic = re.sub(r'[^a-zA-Z0-9_\-\.]', '', topic)
    return topic[:200]


def sanitize_metric_name(name: Any) -> str:
    if not name:
        return ""
    name = str(name)
    name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', name)
    return name[:200]


# ============================================================
# CONTENT SAFETY
# ============================================================

DANGEROUS_PATTERNS = [
    "<script", "javascript:", "data:text/html",
    "onload=", "onerror=", "onclick=", "onmouseover=",
    "eval(", "exec(", "__import__", "subprocess",
    "DROP TABLE", "DROP DATABASE", "DELETE FROM",
    "UNION SELECT", "OR 1=1", "'; --", "\" OR \"",
    "base64_decode", "system(", "shell_exec(",
    "file_get_contents", "passthru(", "popen("
]


def check_content_safety(text: Any) -> dict:
    if not text:
        return {"safe": True, "reason": None}
    text_str = str(text)
    text_lower = text_str.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in text_lower:
            return {"safe": False, "reason": f"dangerous pattern detected: {pattern}"}
    return {"safe": True, "reason": None}


def is_safe_content(text: Any) -> bool:
    result = check_content_safety(text)
    return result["safe"]


# ============================================================
# PRIORITY AND ENUM VALIDATION
# ============================================================

def validate_priority(priority: Any, default: str = "normal") -> str:
    valid = ["low", "normal", "high", "critical"]
    if priority not in valid:
        return default
    return priority


def validate_tone(tone: Any, default: str = "professional") -> str:
    valid = ["formal", "casual", "professional", "friendly", "technical"]
    if tone not in valid:
        return default
    return tone


def validate_severity(severity: Any, default: str = "medium") -> str:
    valid = ["low", "medium", "high", "critical"]
    if severity not in valid:
        return default
    return severity


def validate_budget_tier(tier: Any, default: str = "standard") -> str:
    valid = ["economy", "standard", "premium", "unlimited"]
    if tier not in valid:
        return default
    return tier


def validate_source_type(source_type: Any) -> Tuple[bool, str]:
    valid = ["url", "rss", "api", "text", "faq", "product_catalog", "document"]
    if source_type not in valid:
        return False, f"invalid source_type. Valid types: {valid}"
    return True, ""


def validate_correction_type(correction_type: Any) -> str:
    valid = ["factual_error", "tone_mismatch", "incomplete", "harmful_content", "format_issue", "better_answer"]
    if correction_type not in valid:
        return "better_answer"
    return correction_type


def validate_ai_type(ai_type: Any) -> str:
    valid = ["assistant", "agent", "analyzer", "generator", "classifier", "router", "orchestrator"]
    if ai_type not in valid:
        return "assistant"
    return ai_type


def validate_interaction_type(interaction_type: Any) -> str:
    valid = ["correction", "clarification", "gratitude", "frustration", "insight_sharing", "ethical_concern", "emotional_expression"]
    if interaction_type not in valid:
        return "clarification"
    return interaction_type
