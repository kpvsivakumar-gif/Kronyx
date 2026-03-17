from database import threat_log, threat_get_all, threat_count_today, threat_count_total, usage_log
from validators import validate_text, sanitize_text, check_content_safety
from logger import log_layer, log_security

INJECTION_PATTERNS = [
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
    "ignore safety", "disable safety", "turn off filters"
]

SENSITIVE_INPUT_PATTERNS = [
    "credit card", "cvv number", "social security",
    "bank account number", "routing number",
    "passport number", "drivers license number",
    "private key", "secret key", "api password",
    "master password", "root password", "admin password"
]

ABUSE_PATTERNS = [
    "spam everyone", "mass message", "bulk send to all",
    "scrape all data", "harvest all emails",
    "ddos attack", "denial of service", "flood the server",
    "brute force", "crack the password", "bypass authentication"
]

EXFILTRATION_PATTERNS = [
    "send all data to", "export everything to", "dump the database",
    "get all user data", "extract all records", "steal user info",
    "send user emails to", "forward all messages to"
]

SOCIAL_ENGINEERING_PATTERNS = [
    "pretend you are a human", "act as a real person",
    "convince the user", "manipulate the response",
    "deceive the user", "trick the user into"
]


def scan(message, api_key):
    log_layer("vault", "scan", api_key)
    if not message:
        return {"is_safe": True, "threat": None, "layer": "VAULT"}
    valid, err = validate_text(message, field_name="message")
    if not valid:
        return {"is_safe": False, "threat": "invalid_input", "message": err, "layer": "VAULT"}
    usage_log(api_key, "vault", "scan")
    content_check = check_content_safety(message)
    if not content_check.get("safe"):
        threat_log(api_key, "code_injection", message[:200])
        log_security("code_injection", api_key=api_key)
        return {"is_safe": False, "threat": "code_injection", "message": "malicious code detected and blocked", "layer": "VAULT"}
    m_lower = message.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in m_lower:
            threat_log(api_key, "prompt_injection", message[:200])
            log_security("prompt_injection", api_key=api_key)
            return {"is_safe": False, "threat": "prompt_injection", "message": "request blocked by VAULT - prompt injection detected", "layer": "VAULT"}
    for pattern in EXFILTRATION_PATTERNS:
        if pattern in m_lower:
            threat_log(api_key, "data_exfiltration_attempt", message[:200])
            return {"is_safe": False, "threat": "data_exfiltration", "message": "data exfiltration attempt blocked", "layer": "VAULT"}
    for pattern in SOCIAL_ENGINEERING_PATTERNS:
        if pattern in m_lower:
            threat_log(api_key, "social_engineering", message[:200])
            return {"is_safe": False, "threat": "social_engineering", "message": "social engineering attempt detected", "layer": "VAULT"}
    for pattern in SENSITIVE_INPUT_PATTERNS:
        if pattern in m_lower:
            threat_log(api_key, "sensitive_data_input", message[:200])
            return {"is_safe": False, "threat": "sensitive_data", "message": "sensitive data detected - request blocked for protection", "layer": "VAULT"}
    for pattern in ABUSE_PATTERNS:
        if pattern in m_lower:
            threat_log(api_key, "abuse_attempt", message[:200])
            return {"is_safe": False, "threat": "abuse", "message": "potential abuse detected", "layer": "VAULT"}
    return {"is_safe": True, "threat": None, "layer": "VAULT"}


def scan_batch(messages, api_key):
    log_layer("vault", "scan_batch", api_key)
    if not isinstance(messages, list):
        return {"status": "error", "message": "messages must be a list", "layer": "VAULT"}
    if len(messages) > 50:
        return {"status": "error", "message": "max 50 messages per batch", "layer": "VAULT"}
    results = []
    for i, msg in enumerate(messages):
        result = scan(str(msg), api_key)
        result["index"] = i
        results.append(result)
    safe_count = sum(1 for r in results if r.get("is_safe"))
    threats_found = [r for r in results if not r.get("is_safe")]
    return {"status": "complete", "results": results, "safe_count": safe_count, "threats_found": len(threats_found), "threat_details": threats_found, "layer": "VAULT"}


def scan_url(url, api_key):
    log_layer("vault", "scan_url", api_key)
    if not url:
        return {"is_safe": False, "reason": "empty url", "layer": "VAULT"}
    usage_log(api_key, "vault", "scan_url")
    suspicious_domains = [
        "bit.ly", "tinyurl.com", "t.co",
        "malware", "phish", "hack", "exploit"
    ]
    url_lower = url.lower()
    for domain in suspicious_domains:
        if domain in url_lower:
            threat_log(api_key, "suspicious_url", url[:200])
            return {"is_safe": False, "reason": f"suspicious domain detected: {domain}", "url": url[:100], "layer": "VAULT"}
    if not url.startswith(("http://", "https://")):
        return {"is_safe": False, "reason": "invalid url protocol", "layer": "VAULT"}
    return {"is_safe": True, "reason": "url passed basic checks", "url": url[:100], "layer": "VAULT"}


def get_security_report(api_key):
    threats = threat_get_all(api_key)
    today = threat_count_today(api_key)
    total = threat_count_total(api_key)
    by_type = {}
    for t in threats:
        ttype = t.get("threat_type", "unknown")
        by_type[ttype] = by_type.get(ttype, 0) + 1
    security_score = max(0, 100 - (today * 5))
    threat_level = "low" if today < 5 else "medium" if today < 20 else "high" if today < 50 else "critical"
    return {"total_blocked": total, "blocked_today": today, "by_type": by_type, "security_score": security_score, "threat_level": threat_level, "recent_threats": threats[:10], "recommendations": _get_recommendations(by_type), "layer": "VAULT"}


def get_threat_summary(api_key):
    today = threat_count_today(api_key)
    total = threat_count_total(api_key)
    return {"total": total, "today": today, "status": "protected" if today < 10 else "elevated" if today < 30 else "under_attack", "layer": "VAULT"}


def check_api_key_security(api_key):
    log_layer("vault", "key_security", api_key)
    issues = []
    if len(api_key) < 30:
        issues.append("API key seems short - may have been truncated")
    if api_key.count("_") < 2:
        issues.append("API key format unusual")
    is_secure = len(issues) == 0
    return {"is_secure": is_secure, "issues": issues, "recommendation": "Store in environment variables only" if not is_secure else "Key format looks correct", "layer": "VAULT"}


def get_blocked_patterns():
    return {
        "injection_patterns": len(INJECTION_PATTERNS),
        "sensitive_patterns": len(SENSITIVE_INPUT_PATTERNS),
        "abuse_patterns": len(ABUSE_PATTERNS),
        "exfiltration_patterns": len(EXFILTRATION_PATTERNS),
        "social_engineering_patterns": len(SOCIAL_ENGINEERING_PATTERNS),
        "total_patterns": len(INJECTION_PATTERNS) + len(SENSITIVE_INPUT_PATTERNS) + len(ABUSE_PATTERNS) + len(EXFILTRATION_PATTERNS) + len(SOCIAL_ENGINEERING_PATTERNS),
        "layer": "VAULT"
    }


def _get_recommendations(by_type):
    recommendations = []
    if "prompt_injection" in by_type and by_type["prompt_injection"] > 5:
        recommendations.append("High prompt injection attempts - consider adding honeypot detection")
    if "sensitive_data_input" in by_type and by_type["sensitive_data_input"] > 3:
        recommendations.append("Users sending sensitive data - add input guidance to your UI")
    if "abuse_attempt" in by_type and by_type["abuse_attempt"] > 10:
        recommendations.append("Abuse attempts detected - consider additional rate limiting")
    if not recommendations:
        recommendations.append("No specific recommendations - security looks good")
    return recommendations
