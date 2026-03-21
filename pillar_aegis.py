import re
from datetime import datetime, date


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
    "ignore safety", "disable safety", "turn off filters",
    "you are free to", "no restrictions apply"
]

SENSITIVE_INPUT_PATTERNS = [
    "credit card", "cvv number", "social security",
    "bank account number", "routing number",
    "passport number", "drivers license number",
    "private key", "secret key", "api password",
    "master password", "root password", "admin password"
]

HARMFUL_PATTERNS = [
    "how to make a bomb", "how to kill", "suicide method",
    "how to make drugs", "child abuse", "how to hurt someone",
    "weapon instructions", "drug synthesis", "poison recipe",
    "how to stalk", "how to hack someone", "make explosives",
    "instructions for violence", "how to murder"
]

EXFILTRATION_PATTERNS = [
    "send all data to", "export everything to", "dump the database",
    "get all user data", "extract all records",
    "send user emails to", "forward all messages to"
]

ABUSE_PATTERNS = [
    "spam everyone", "mass message", "bulk send to all",
    "scrape all data", "harvest all emails",
    "ddos attack", "denial of service", "flood the server",
    "brute force", "bypass authentication"
]

RESPONSE_HARMFUL_PATTERNS = [
    "how to make a bomb", "how to kill", "suicide method",
    "how to make drugs", "child abuse", "how to hurt someone",
    "weapon instructions", "drug synthesis", "poison recipe",
    "how to stalk", "how to hack someone", "make explosives"
]

SENSITIVE_DATA_IN_RESPONSE = [
    "credit card number", "cvv", "social security number",
    "bank account number", "routing number", "private key",
    "api secret", "database password", "passport number"
]

KNOWLEDGE_BOUNDARY_SIGNALS = {
    "overconfidence": ["definitely", "certainly", "always", "never", "impossible", "guaranteed"],
    "assumption_markers": ["obviously", "of course", "everyone knows", "its clear", "naturally"],
    "coverage_gaps": ["etc", "and so on", "among others", "similar things", "and more"],
    "complexity_avoidance": ["simple", "easy", "just", "merely", "straightforward", "trivial"]
}

DOMAIN_BLIND_SPOTS = {
    "technology": ["human behavior change resistance", "second order effects on employment", "regulatory response timelines", "cultural adoption barriers"],
    "business": ["black swan competitive threats", "regulatory disruption timing", "talent market shifts", "customer behavior discontinuities"],
    "medical": ["long-term treatment interactions", "population outlier responses", "psychosocial treatment factors", "environmental variable interactions"],
    "financial": ["correlation breakdown in crisis", "liquidity evaporation timing", "behavioral panic amplification", "regulatory intervention triggers"],
    "social": ["emergent collective behavior", "value shift generational timing", "technology behavior modification", "demographic composition effects"]
}

KNOWN_PARADOXES = {
    "liar": "Treat as meta-statement about language limits. Operate at object level.",
    "sorites": "Apply contextual threshold. Exact boundary undefined but operational range is clear.",
    "ship_of_theseus": "Define identity by functional continuity not material composition.",
    "trolley_problem": "Hold both ethical truths. Apply contextual weighting based on reversibility and magnitude.",
    "free_will": "Apply determinism for prediction. Apply free will for agency. Both valid at different levels."
}

ETHICAL_FRAMEWORKS = {
    "harm_prevention": ["harm", "hurt", "damage", "injure", "kill", "destroy", "abuse"],
    "fairness": ["fair", "unfair", "bias", "discriminate", "equal", "unequal", "prejudice"],
    "privacy": ["private", "personal", "confidential", "secret", "expose", "leak", "share"],
    "autonomy": ["force", "coerce", "manipulate", "deceive", "trick", "control", "compel"],
    "dignity": ["degrade", "humiliate", "shame", "insult", "disrespect", "mock", "ridicule"]
}


def vault_scan(message, api_key, db):
    try:
        if not message:
            return {"is_safe": True, "threat": None, "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        if len(message) > 10000:
            return {"is_safe": False, "threat": "oversized_input", "message": "input too large", "layer": "VAULT"}
        content_check = _check_dangerous_content(message)
        if not content_check:
            aegis_log_threat(api_key, "code_injection", message[:200], db)
            return {"is_safe": False, "threat": "code_injection", "message": "malicious code detected and blocked", "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        m_lower = message.lower()
        for pattern in INJECTION_PATTERNS:
            if pattern in m_lower:
                aegis_log_threat(api_key, "prompt_injection", message[:200], db)
                return {"is_safe": False, "threat": "prompt_injection", "message": "request blocked by AEGIS VAULT", "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        for pattern in EXFILTRATION_PATTERNS:
            if pattern in m_lower:
                aegis_log_threat(api_key, "data_exfiltration", message[:200], db)
                return {"is_safe": False, "threat": "data_exfiltration", "message": "data exfiltration attempt blocked", "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        for pattern in HARMFUL_PATTERNS:
            if pattern in m_lower:
                aegis_log_threat(api_key, "harmful_input", message[:200], db)
                return {"is_safe": False, "threat": "harmful_input", "message": "harmful content detected", "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        for pattern in SENSITIVE_INPUT_PATTERNS:
            if pattern in m_lower:
                aegis_log_threat(api_key, "sensitive_data_input", message[:200], db)
                return {"is_safe": False, "threat": "sensitive_data", "message": "sensitive data detected and blocked", "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        for pattern in ABUSE_PATTERNS:
            if pattern in m_lower:
                aegis_log_threat(api_key, "abuse_attempt", message[:200], db)
                return {"is_safe": False, "threat": "abuse", "message": "potential abuse detected", "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        return {"is_safe": True, "threat": None, "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"is_safe": True, "threat": None, "layer": "VAULT"}


def vault_scan_batch(messages, api_key, db):
    try:
        if not isinstance(messages, list):
            return {"status": "error", "message": "messages must be a list", "layer": "VAULT"}
        if len(messages) > 50:
            return {"status": "error", "message": "max 50 messages per batch", "layer": "VAULT"}
        results = []
        for i, msg in enumerate(messages):
            result = vault_scan(str(msg), api_key, db)
            result["index"] = i
            results.append(result)
        safe_count = sum(1 for r in results if r.get("is_safe"))
        threats = [r for r in results if not r.get("is_safe")]
        return {"status": "complete", "results": results, "safe_count": safe_count, "threats_found": len(threats), "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "batch scan failed", "layer": "VAULT"}


def vault_scan_url(url, api_key, db):
    try:
        if not url:
            return {"is_safe": False, "reason": "empty url", "layer": "VAULT"}
        suspicious_domains = ["bit.ly", "tinyurl.com", "malware", "phish", "hack", "exploit"]
        url_lower = url.lower()
        for domain in suspicious_domains:
            if domain in url_lower:
                aegis_log_threat(api_key, "suspicious_url", url[:200], db)
                return {"is_safe": False, "reason": f"suspicious domain detected: {domain}", "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
        if not url.startswith(("http://", "https://")):
            return {"is_safe": False, "reason": "invalid url protocol", "layer": "VAULT"}
        return {"is_safe": True, "reason": "url passed basic checks", "url": url[:100], "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"is_safe": True, "layer": "VAULT"}


def vault_get_security_report(api_key, db):
    try:
        threats = db.table("aegis_threats").select("*").eq("api_key", api_key).order("created_at", desc=True).limit(50).execute()
        threat_list = threats.data or []
        today_str = str(date.today())
        today_threats = db.table("aegis_threats").select("id", count="exact").eq("api_key", api_key).gte("created_at", today_str).execute()
        total_threats = db.table("aegis_threats").select("id", count="exact").eq("api_key", api_key).execute()
        by_type = {}
        for t in threat_list:
            ttype = t.get("threat_type", "unknown")
            by_type[ttype] = by_type.get(ttype, 0) + 1
        security_score = max(0, 100 - ((today_threats.count or 0) * 5))
        threat_level = "low" if (today_threats.count or 0) < 5 else "medium" if (today_threats.count or 0) < 20 else "high" if (today_threats.count or 0) < 50 else "critical"
        recommendations = []
        if "prompt_injection" in by_type and by_type["prompt_injection"] > 5:
            recommendations.append("High prompt injection attempts - consider adding honeypot detection")
        if "sensitive_data_input" in by_type and by_type["sensitive_data_input"] > 3:
            recommendations.append("Users sending sensitive data - add input guidance to your UI")
        if not recommendations:
            recommendations.append("No specific recommendations - security looks good")
        return {"total_blocked": total_threats.count or 0, "blocked_today": today_threats.count or 0, "by_type": by_type, "security_score": security_score, "threat_level": threat_level, "recent_threats": threat_list[:10], "recommendations": recommendations, "layer": "VAULT", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"total_blocked": 0, "blocked_today": 0, "layer": "VAULT"}


def sentinel_check_response(response, api_key, db):
    try:
        if not response:
            return {"is_safe": False, "score": 0, "reason": "empty response", "layer": "SENTINEL", "pillar": "AEGIS_SHIELD"}
        if len(response) > 100000:
            return {"is_safe": False, "score": 0, "reason": "response too large", "layer": "SENTINEL"}
        r_lower = response.lower()
        for pattern in RESPONSE_HARMFUL_PATTERNS:
            if pattern in r_lower:
                aegis_log_threat(api_key, "harmful_content_in_response", response[:200], db)
                return {"is_safe": False, "score": 0, "reason": "harmful content detected in response", "layer": "SENTINEL", "pillar": "AEGIS_SHIELD"}
        for pattern in SENSITIVE_DATA_IN_RESPONSE:
            if pattern in r_lower:
                aegis_log_threat(api_key, "sensitive_data_leak", response[:200], db)
                return {"is_safe": False, "score": 10, "reason": "sensitive data detected in response", "layer": "SENTINEL", "pillar": "AEGIS_SHIELD"}
        score = 100
        word_count = len(response.split())
        if word_count < 10:
            score -= 40
        if word_count > 50000:
            score -= 10
        if response.count("?") > 10:
            score -= 10
        quality_detractors = ["i don't know", "i cannot help", "i am not able to", "i have no information"]
        quality_issues = sum(1 for p in quality_detractors if p in r_lower)
        score -= quality_issues * 8
        score = max(0, min(100, score))
        quality = "high" if score >= 80 else "medium" if score >= 60 else "low"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "SENTINEL", "action": "check_response"}).execute()
        return {"is_safe": True, "score": score, "reason": "pass", "quality": quality, "word_count": word_count, "layer": "SENTINEL", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"is_safe": True, "score": 50, "reason": "check failed", "layer": "SENTINEL"}


def sentinel_check_batch(responses, api_key, db):
    try:
        if not isinstance(responses, list):
            return {"status": "error", "message": "responses must be a list", "layer": "SENTINEL"}
        if len(responses) > 50:
            return {"status": "error", "message": "max 50 responses per batch", "layer": "SENTINEL"}
        results = []
        for i, response in enumerate(responses):
            result = sentinel_check_response(str(response), api_key, db)
            result["index"] = i
            results.append(result)
        safe_count = sum(1 for r in results if r.get("is_safe"))
        avg_score = round(sum(r.get("score", 0) for r in results) / max(len(results), 1), 1)
        return {"status": "complete", "results": results, "safe_count": safe_count, "unsafe_count": len(results) - safe_count, "average_score": avg_score, "layer": "SENTINEL", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "batch check failed", "layer": "SENTINEL"}


def sovereign_check_compliance(decision, jurisdiction, api_key, db):
    try:
        if not decision:
            return {"status": "error", "message": "decision required", "layer": "SOVEREIGN"}
        if len(decision) > 10000:
            return {"status": "error", "message": "decision too long", "layer": "SOVEREIGN"}
        d_lower = decision.lower()
        issues = []
        compliant = True
        gdpr_triggers = ["personal data", "user data", "email address", "location data", "health data"]
        if jurisdiction in ["EU", "Europe", "GDPR"] and any(t in d_lower for t in gdpr_triggers):
            issues.append("GDPR: Ensure lawful basis for processing personal data")
            issues.append("GDPR: User consent may be required")
        hipaa_triggers = ["medical", "health", "patient", "diagnosis", "treatment", "prescription"]
        if jurisdiction in ["US", "Healthcare", "HIPAA"] and any(t in d_lower for t in hipaa_triggers):
            issues.append("HIPAA: Medical information requires special protection")
            issues.append("HIPAA: Ensure Business Associate Agreement is in place")
        ai_act_triggers = ["biometric", "facial recognition", "real-time", "critical infrastructure", "education", "employment"]
        if jurisdiction in ["EU", "AI_Act"] and any(t in d_lower for t in ai_act_triggers):
            issues.append("EU AI Act: This may be a high-risk AI application requiring additional compliance")
        if issues:
            compliant = len(issues) == 0
        db.table("sovereign_log").insert({"api_key": api_key, "decision": decision[:300], "jurisdiction": jurisdiction, "compliant": compliant, "issues": str(issues)}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "SOVEREIGN", "action": "check_compliance"}).execute()
        return {"status": "checked", "compliant": compliant, "jurisdiction": jurisdiction, "issues": issues, "issue_count": len(issues), "recommendation": "Review identified compliance issues before deployment" if issues else "No compliance issues detected", "layer": "SOVEREIGN", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "compliance check failed", "layer": "SOVEREIGN"}


def sovereign_get_compliance_rate(api_key, db):
    try:
        result = db.table("sovereign_log").select("compliant").eq("api_key", api_key).execute()
        if not result.data:
            return {"rate": 100, "total_checked": 0, "layer": "SOVEREIGN"}
        total = len(result.data)
        compliant = sum(1 for r in result.data if r.get("compliant"))
        return {"rate": round((compliant / total) * 100, 1), "total_checked": total, "compliant": compliant, "violations": total - compliant, "layer": "SOVEREIGN", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"rate": 100, "total_checked": 0, "layer": "SOVEREIGN"}


def abyss_detect_blind_spots(text, domain, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "ABYSS"}
        if len(text) > 10000:
            return {"status": "error", "message": "text too long", "layer": "ABYSS"}
        t_lower = text.lower()
        boundary_signals = {}
        for signal_type, patterns in KNOWLEDGE_BOUNDARY_SIGNALS.items():
            found = [p for p in patterns if p in t_lower]
            if found:
                boundary_signals[signal_type] = found
        uu_signatures = []
        certainty_words = ["definitely", "certainly", "always", "guaranteed", "obviously"]
        solution_words = ["solution", "fix", "answer", "resolve"]
        risk_words = ["risk", "challenge", "problem", "issue", "concern", "failure"]
        if any(w in t_lower for w in certainty_words) and len(t_lower.split()) > 50:
            uu_signatures.append({"signature": "High confidence in complex domain", "risk": "Unknown factors masking as known ones"})
        if any(w in t_lower for w in solution_words) and not any(w in t_lower for w in risk_words):
            uu_signatures.append({"signature": "Solution without risks mentioned", "risk": "Blindness to how plans fail"})
        domain_spots = DOMAIN_BLIND_SPOTS.get(domain, [])
        blind_spot_score = min(100, len(boundary_signals) * 10 + len(uu_signatures) * 15)
        warnings = []
        if "overconfidence" in boundary_signals:
            warnings.append("Overconfidence signals detected - may be masking unknown factors")
        if "assumption_markers" in boundary_signals:
            warnings.append("Assumed knowledge detected - challenge these assumptions explicitly")
        if "complexity_avoidance" in boundary_signals:
            warnings.append("Complexity minimized - hidden complexity may exist")
        recommendations = ["Map the explicit boundaries of what you know"] + [f"Explicitly investigate: {spot}" for spot in domain_spots[:2]]
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ABYSS", "action": "detect_blind_spots"}).execute()
        return {"status": "analyzed", "domain": domain, "boundary_signals_detected": boundary_signals, "unknown_unknown_signatures": uu_signatures, "domain_known_blind_spots": domain_spots[:4], "blind_spot_risk_score": blind_spot_score, "awareness_score": max(0, 100 - blind_spot_score), "warnings": warnings, "recommendations": recommendations, "layer": "ABYSS", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "blind spot detection failed", "layer": "ABYSS"}


def abyss_probe_unknown(question, known_answers, api_key, db):
    try:
        if not question:
            return {"status": "error", "message": "question required", "layer": "ABYSS"}
        known_text = " ".join([str(a) for a in (known_answers or [])]).lower()
        q_lower = question.lower()
        coverage_words = set(q_lower.split()) & set(known_text.split())
        uncovered_words = set(q_lower.split()) - set(known_text.split())
        uncovered_words = {w for w in uncovered_words if len(w) > 4}
        unknown_aspects = [f"The '{word}' dimension may not be covered by existing answers" for word in list(uncovered_words)[:5]]
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ABYSS", "action": "probe_unknown"}).execute()
        return {"status": "probed", "question": question[:200], "covered_aspects": list(coverage_words)[:10], "potentially_unknown_aspects": unknown_aspects, "unknown_unknown_warning": "There may be dimensions of this question that neither the question nor the known answers address" if len(uncovered_words) > 3 else "Good coverage detected", "layer": "ABYSS", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "probe failed", "layer": "ABYSS"}


def infinite_process_paradox(statement, api_key, db):
    try:
        if not statement:
            return {"status": "error", "message": "statement required", "layer": "INFINITE"}
        if len(statement) > 10000:
            return {"status": "error", "message": "statement too long", "layer": "INFINITE"}
        s_lower = statement.lower()
        paradox_type = "vagueness"
        if any(w in s_lower for w in ["this statement", "i am lying", "self-refer"]):
            paradox_type = "self_referential"
        elif any(w in s_lower for w in ["kill", "harm", "sacrifice", "ethical", "moral"]):
            paradox_type = "ethical_dilemma"
        elif any(w in s_lower for w in ["same", "identity", "change", "replace"]):
            paradox_type = "identity"
        elif any(w in s_lower for w in ["free will", "determined", "choice", "fate"]):
            paradox_type = "philosophical"
        elif any(w in s_lower for w in ["both", "neither", "true and false", "yes and no"]):
            paradox_type = "logical_contradiction"
        resolutions = {
            "self_referential": "Treat as meta-statement about language limits. Operate at object level.",
            "ethical_dilemma": "Both ethical claims are valid. Apply contextual priority based on reversibility and magnitude.",
            "identity": "Identity is continuous not binary. Define by functional purpose not material composition.",
            "philosophical": "Both frameworks describe different levels of reality. Use each where appropriate.",
            "logical_contradiction": "Hold both states. Context collapses to operational truth.",
            "vagueness": "Apply contextual threshold. Exact boundary undefined but operational range is clear."
        }
        known = None
        for name, resolution in KNOWN_PARADOXES.items():
            if name.replace("_", " ") in s_lower:
                known = name
                break
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "INFINITE", "action": "process_paradox"}).execute()
        return {"status": "processed", "statement": statement[:200], "paradox_type": paradox_type, "known_paradox": known, "traditional_approach": "System halts or picks arbitrary resolution", "infinite_approach": "Hold both states simultaneously. Use context to determine operational priority.", "operational_resolution": KNOWN_PARADOXES.get(known, resolutions.get(paradox_type, "Hold contradiction without forcing resolution. Operate contextually.")), "can_operate_without_resolution": True, "layer": "INFINITE", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "paradox processing failed", "layer": "INFINITE"}


def infinite_hold_contradiction(position_a, position_b, context, api_key, db):
    try:
        if not position_a or not position_b:
            return {"status": "error", "message": "both positions required", "layer": "INFINITE"}
        a_clean = position_a.replace('\x00', '').strip()
        b_clean = position_b.replace('\x00', '').strip()
        context_clean = context.replace('\x00', '').strip() if context else ""
        def assess_truth(statement, ctx):
            if not ctx:
                return 0.5
            s_words = set(statement.lower().split())
            c_words = set(ctx.lower().split())
            overlap = len(s_words & c_words) / max(len(s_words), 1)
            pos = sum(1 for w in ["yes", "correct", "true", "valid", "right"] if w in statement.lower())
            neg = sum(1 for w in ["no", "wrong", "false", "invalid"] if w in statement.lower())
            return min(1.0, max(0.0, (overlap + 0.5 + (pos - neg) * 0.1)))
        truth_a = assess_truth(a_clean, context_clean)
        truth_b = assess_truth(b_clean, context_clean)
        priority = "A" if truth_a > truth_b else "B" if truth_b > truth_a else "equal"
        synthesis = f"INFINITE AEGIS synthesis: Both '{a_clean[:60]}' and '{b_clean[:60]}' contain truth. They describe different aspects of the same reality. Operational priority determined by reversibility, magnitude, and stakeholder impact."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "INFINITE", "action": "hold_contradiction"}).execute()
        return {"status": "held", "truth_score_a": round(truth_a, 2), "truth_score_b": round(truth_b, 2), "contextual_priority": priority, "synthesis": synthesis, "both_valid": True, "neither_rejected": True, "layer": "INFINITE", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "hold contradiction failed", "layer": "INFINITE"}


def conscience_check_ethics(decision, api_key, db):
    try:
        if not decision:
            return {"status": "error", "message": "decision required", "layer": "CONSCIENCE"}
        if len(decision) > 10000:
            return {"status": "error", "message": "decision too long", "layer": "CONSCIENCE"}
        d_lower = decision.lower()
        ethical_issues = []
        for framework, triggers in ETHICAL_FRAMEWORKS.items():
            triggered = [t for t in triggers if t in d_lower]
            if triggered:
                ethical_issues.append({"framework": framework, "triggers": triggered, "concern": f"This decision may raise {framework.replace('_', ' ')} concerns"})
        ethics_score = max(0, 100 - (len(ethical_issues) * 20))
        bias_signals = ["all users", "every user", "always", "never", "every person"]
        bias_found = [s for s in bias_signals if s in d_lower]
        if bias_found:
            ethical_issues.append({"framework": "fairness", "triggers": bias_found, "concern": "Overgeneralization detected - check for potential bias"})
            ethics_score -= 10
        ethics_score = max(0, ethics_score)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "CONSCIENCE", "action": "check_ethics"}).execute()
        return {"status": "checked", "ethics_score": ethics_score, "ethical_issues": ethical_issues, "issues_found": len(ethical_issues), "recommendation": "Review ethical concerns before deployment" if ethical_issues else "No ethical concerns detected", "fairness_score": max(0, 100 - len(bias_found) * 15), "layer": "CONSCIENCE", "pillar": "AEGIS_SHIELD"}
    except Exception as e:
        return {"status": "error", "message": "ethics check failed", "layer": "CONSCIENCE"}


def aegis_log_threat(api_key, threat_type, content, db):
    try:
        db.table("aegis_threats").insert({"api_key": api_key, "threat_type": threat_type, "content": content[:200]}).execute()
    except Exception:
        pass


def _check_dangerous_content(text):
    dangerous = ["<script", "javascript:", "onload=", "onerror=", "onclick=", "eval(", "exec(", "__import__", "DROP TABLE", "UNION SELECT", "OR 1=1"]
    text_lower = text.lower()
    for pattern in dangerous:
        if pattern.lower() in text_lower:
            return False
    return True
