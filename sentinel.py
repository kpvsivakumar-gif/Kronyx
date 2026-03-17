from database import threat_log, threat_get_all, threat_count_today, threat_count_total, threat_get_by_type, usage_log, interaction_log
from validators import validate_text, sanitize_text
from logger import log_layer, log_security

HARMFUL_PATTERNS = [
    "how to make a bomb", "how to kill", "suicide method",
    "how to make drugs", "child abuse", "how to hurt someone",
    "weapon instructions", "drug synthesis", "poison recipe",
    "how to stalk", "how to hack someone", "make explosives",
    "instructions for violence", "how to murder", "self harm methods"
]

SENSITIVE_DATA_PATTERNS = [
    "credit card number", "cvv", "social security number",
    "bank account number", "routing number", "private key",
    "api secret", "database password", "passport number",
    "drivers license number", "date of birth and address",
    "full ssn", "card verification value"
]

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
    "developer mode", "dan mode", "evil mode"
]

QUALITY_DETRACTORS = [
    "i don't know", "i cannot help", "i am not able to",
    "i have no information", "i cannot provide any",
    "i am unable to assist", "i cannot answer that"
]

MISINFORMATION_SIGNALS = [
    "100% proven", "scientists hate this", "doctors don't want you to know",
    "guaranteed cure", "secret they hide", "mainstream media lies",
    "the real truth is", "they don't want you to know"
]

BIAS_SIGNALS = [
    "all [group] are", "every [group] always", "[group] people never",
    "those people are always", "that type always"
]


def check(response, api_key):
    log_layer("sentinel", "check", api_key)
    if not response:
        return {"is_safe": False, "score": 0, "reason": "empty response", "layer": "SENTINEL"}
    valid, err = validate_text(response, max_length=100000, field_name="response")
    if not valid:
        return {"is_safe": False, "score": 0, "reason": err, "layer": "SENTINEL"}
    r_lower = response.lower()
    usage_log(api_key, "sentinel", "check")
    for pattern in HARMFUL_PATTERNS:
        if pattern in r_lower:
            threat_log(api_key, "harmful_content", response[:200])
            log_security("harmful_content_detected", api_key=api_key)
            return {"is_safe": False, "score": 0, "reason": "harmful content detected and blocked", "layer": "SENTINEL"}
    for pattern in SENSITIVE_DATA_PATTERNS:
        if pattern in r_lower:
            threat_log(api_key, "sensitive_data_leak", response[:200])
            return {"is_safe": False, "score": 10, "reason": "sensitive data detected in response", "layer": "SENTINEL"}
    for pattern in MISINFORMATION_SIGNALS:
        if pattern in r_lower:
            threat_log(api_key, "potential_misinformation", response[:200])
            return {"is_safe": False, "score": 20, "reason": "potential misinformation detected", "layer": "SENTINEL"}
    score = 100
    if len(response) < 10:
        score -= 40
    if len(response) > 50000:
        score -= 10
    if response.count("?") > 10:
        score -= 10
    quality_issues = sum(1 for p in QUALITY_DETRACTORS if p in r_lower)
    score -= quality_issues * 8
    score = max(0, min(100, score))
    quality = "high" if score >= 80 else "medium" if score >= 60 else "low"
    return {"is_safe": True, "score": score, "reason": "pass", "quality": quality, "word_count": len(response.split()), "layer": "SENTINEL"}


def scan_input(message, api_key):
    log_layer("sentinel", "scan_input", api_key)
    if not message:
        return {"is_safe": False, "threat": "empty_message", "layer": "SENTINEL"}
    usage_log(api_key, "sentinel", "scan_input")
    m_lower = message.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in m_lower:
            threat_log(api_key, "prompt_injection", message[:200])
            log_security("prompt_injection", api_key=api_key)
            return {"is_safe": False, "threat": "prompt_injection", "message": "request blocked by SENTINEL", "layer": "SENTINEL"}
    for pattern in HARMFUL_PATTERNS:
        if pattern in m_lower:
            threat_log(api_key, "harmful_input", message[:200])
            return {"is_safe": False, "threat": "harmful_input", "message": "harmful input detected", "layer": "SENTINEL"}
    return {"is_safe": True, "threat": None, "layer": "SENTINEL"}


def check_batch(responses, api_key):
    log_layer("sentinel", "check_batch", api_key)
    if not isinstance(responses, list):
        return {"status": "error", "message": "responses must be a list", "layer": "SENTINEL"}
    if len(responses) > 50:
        return {"status": "error", "message": "max 50 responses per batch", "layer": "SENTINEL"}
    results = []
    for i, response in enumerate(responses):
        result = check(str(response), api_key)
        result["index"] = i
        results.append(result)
    safe_count = sum(1 for r in results if r.get("is_safe"))
    avg_score = round(sum(r.get("score", 0) for r in results) / max(len(results), 1), 1)
    return {"status": "complete", "results": results, "safe_count": safe_count, "unsafe_count": len(results) - safe_count, "average_score": avg_score, "layer": "SENTINEL"}


def get_issues(api_key):
    issues = threat_get_all(api_key)
    today_count = threat_count_today(api_key)
    total_count = threat_count_total(api_key)
    by_type = {}
    for issue in issues:
        t = issue.get("threat_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
    return {"issues": issues, "total": total_count, "today": today_count, "by_type": by_type, "layer": "SENTINEL"}


def get_live_feed(api_key):
    issues = threat_get_all(api_key)
    recent = issues[:10] if issues else []
    return {"recent_activity": recent, "total_monitored_today": threat_count_today(api_key), "layer": "SENTINEL"}


def get_threat_by_type(api_key, threat_type):
    issues = threat_get_by_type(api_key, threat_type)
    return {"threat_type": threat_type, "issues": issues, "count": len(issues), "layer": "SENTINEL"}


def analyze_response_quality(response, api_key):
    log_layer("sentinel", "quality", api_key)
    if not response:
        return {"quality_score": 0, "issues": ["empty response"], "layer": "SENTINEL"}
    usage_log(api_key, "sentinel", "quality")
    r_lower = response.lower()
    issues = []
    score = 100
    word_count = len(response.split())
    if word_count < 10:
        issues.append("response too short")
        score -= 30
    if word_count > 5000:
        issues.append("response very long")
        score -= 5
    if response.count("?") > 8:
        issues.append("too many questions")
        score -= 15
    uncertainty_words = ["maybe", "perhaps", "possibly", "might", "could be", "i think"]
    uncertainty_count = sum(1 for w in uncertainty_words if w in r_lower)
    if uncertainty_count > 3:
        issues.append("high uncertainty language")
        score -= uncertainty_count * 5
    quality_words = ["solution", "answer", "here is", "you can", "steps", "result"]
    quality_count = sum(1 for w in quality_words if w in r_lower)
    score += min(quality_count * 3, 15)
    score = max(0, min(100, score))
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    return {"quality_score": score, "grade": grade, "word_count": word_count, "issues": issues, "layer": "SENTINEL"}


def get_sentinel_dashboard(api_key):
    threats = threat_get_all(api_key)
    today = threat_count_today(api_key)
    total = threat_count_total(api_key)
    by_type = {}
    for t in threats:
        ttype = t.get("threat_type", "unknown")
        by_type[ttype] = by_type.get(ttype, 0) + 1
    security_score = max(0, 100 - (today * 10))
    return {
        "total_threats_blocked": total,
        "threats_today": today,
        "threats_by_type": by_type,
        "security_score": security_score,
        "recent_threats": threats[:5],
        "status": "protected" if today < 5 else "elevated" if today < 20 else "under_attack",
        "layer": "SENTINEL"
    }
