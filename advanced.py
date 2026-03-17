from database import oracle_log, oracle_get_history, genome_save, genome_get, nexus_source_save, nexus_sources_get, usage_log, interaction_log, memory_insert, memory_search
from validators import validate_text, validate_user_id, sanitize_text
from logger import log_layer, log_error
import httpx
import re

INTENT_PATTERNS = {
    "complaint": ["not working", "broken", "issue", "problem", "wrong", "error", "failed", "terrible", "awful", "disappointed", "frustrated", "annoyed", "cant", "doesn't work"],
    "purchase_intent": ["buy", "price", "cost", "how much", "order", "purchase", "get one", "available", "stock", "shipping", "delivery", "want to get"],
    "support_needed": ["help", "how do i", "how to", "can you", "explain", "confused", "don't understand", "not sure", "what does", "what is", "guide me"],
    "urgent": ["urgent", "asap", "immediately", "emergency", "critical", "now", "right now", "quickly", "as soon as possible", "important", "need now"],
    "comparison": ["vs", "versus", "compare", "difference", "better", "which one", "or", "alternative", "instead of", "over"],
    "refund_return": ["refund", "return", "cancel", "money back", "exchange", "replace", "broken item", "want refund"],
    "feedback": ["feedback", "review", "rating", "experience", "thoughts", "opinion", "suggest", "improve", "idea"],
    "general_inquiry": []
}

EMOTION_PATTERNS = {
    "frustrated": ["!", "!!!", "why", "still", "again", "always", "never", "cant believe"],
    "excited": ["amazing", "great", "love", "awesome", "fantastic", "excellent", "wow", "incredible"],
    "confused": ["?", "??", "not sure", "unclear", "confusing", "don't get", "what do you mean"],
    "neutral": []
}

APPROACH_MAP = {
    "complaint": "Be empathetic, acknowledge the issue, provide clear solution and timeline",
    "purchase_intent": "Be helpful, highlight value, provide clear pricing and next steps",
    "support_needed": "Be clear, use simple language, give step-by-step guidance",
    "urgent": "Respond immediately, be direct, prioritize their need above all else",
    "comparison": "Be objective, provide clear differences, help them make the right decision",
    "refund_return": "Be understanding, explain process clearly, resolve quickly",
    "feedback": "Be appreciative, acknowledge their input, show you genuinely care",
    "general_inquiry": "Be informative, clear and genuinely helpful"
}

TONE_MODIFIERS = {
    "formal": {"style": "Use formal language, avoid contractions, be precise", "avoid": ["hey", "hi there", "sure thing", "no problem", "yep"]},
    "casual": {"style": "Be friendly and conversational, use contractions freely", "avoid": ["Greetings", "Furthermore", "Consequently", "Nevertheless"]},
    "professional": {"style": "Be clear, direct and professional", "avoid": ["totally", "awesome", "super", "kinda"]},
    "friendly": {"style": "Be warm, encouraging and supportive", "avoid": []},
    "technical": {"style": "Be precise, use technical terminology, be detailed", "avoid": ["kinda", "sorta", "maybe"]}
}

CONCEPTUAL_STRUCTURES = {
    "containment": ["in", "inside", "within", "contain", "hold", "include", "part of"],
    "causation": ["because", "cause", "result", "therefore", "leads to", "creates", "produces"],
    "opposition": ["but", "however", "despite", "contrast", "opposite", "against", "versus"],
    "sequence": ["first", "then", "next", "after", "before", "finally", "subsequently"],
    "similarity": ["like", "similar", "same", "also", "both", "equally", "likewise"],
    "intensity": ["very", "extremely", "highly", "deeply", "strongly", "significantly"],
    "uncertainty": ["maybe", "perhaps", "possibly", "might", "could", "uncertain"],
    "negation": ["not", "never", "no", "without", "lack", "absence", "missing"]
}

SUPPORTED_SOURCE_TYPES = ["url", "rss", "api", "text", "faq", "product_catalog"]


def oracle_predict_intent(message, user_id, api_key):
    log_layer("oracle", "predict_intent", api_key)
    if not message:
        return {"status": "error", "message": "message required", "layer": "ORACLE"}
    valid, err = validate_text(message, field_name="message")
    if not valid:
        return {"status": "error", "message": err, "layer": "ORACLE"}
    usage_log(api_key, "oracle", "predict_intent")
    message_clean = sanitize_text(message)
    m_lower = message_clean.lower()
    intent_scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = sum(1 for p in patterns if p in m_lower)
        if score > 0:
            intent_scores[intent] = score
    primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "general_inquiry"
    emotion = "neutral"
    for em, patterns in EMOTION_PATTERNS.items():
        if any(p in m_lower for p in patterns):
            emotion = em
            break
    urgent = any(word in m_lower for word in INTENT_PATTERNS["urgent"])
    predicted_intent = f"User needs {primary_intent.replace('_', ' ')}"
    oracle_log(api_key, user_id, message_clean[:200], predicted_intent)
    return {
        "status": "success",
        "original_message": message_clean,
        "predicted_intent": primary_intent,
        "intent_explanation": predicted_intent,
        "emotion": emotion,
        "is_urgent": urgent,
        "recommended_approach": APPROACH_MAP.get(primary_intent, "Be helpful and clear"),
        "confidence": min(100, max(20, len(intent_scores) * 30 + 40)),
        "layer": "ORACLE"
    }


def oracle_get_intent_history(api_key, user_id):
    log_layer("oracle", "history", api_key)
    history = oracle_get_history(api_key, user_id)
    return {"user_id": user_id, "predictions": history, "total": len(history), "layer": "ORACLE"}


def oracle_analyze_pattern(messages, api_key):
    log_layer("oracle", "analyze_pattern", api_key)
    if not messages:
        return {"pattern": "no_data", "layer": "ORACLE"}
    usage_log(api_key, "oracle", "analyze_pattern")
    intents = []
    for msg in messages[:20]:
        if isinstance(msg, str):
            result = oracle_predict_intent(msg, "analysis", api_key)
            intents.append(result.get("predicted_intent", "general_inquiry"))
    from collections import Counter
    intent_count = Counter(intents)
    dominant = intent_count.most_common(1)[0][0] if intent_count else "general_inquiry"
    return {"dominant_intent": dominant, "intent_distribution": dict(intent_count), "message_count": len(messages), "layer": "ORACLE"}


def genome_build_profile(business_name, business_type, tone, vocabulary, personality_traits, preferred_words, avoid_words, api_key):
    log_layer("genome", "build_profile", api_key)
    valid, err = validate_text(business_name, max_length=200, field_name="business_name")
    if not valid:
        return {"status": "error", "message": err, "layer": "GENOME"}
    if tone not in TONE_MODIFIERS:
        tone = "professional"
    profile = {
        "business_name": sanitize_text(business_name),
        "business_type": sanitize_text(business_type)[:200],
        "tone": tone,
        "vocabulary": vocabulary or "general",
        "personality_traits": personality_traits[:10] if personality_traits else ["helpful"],
        "preferred_words": preferred_words[:20] if preferred_words else [],
        "avoid_words": avoid_words[:20] if avoid_words else [],
        "communication_style": TONE_MODIFIERS.get(tone, {}).get("style", ""),
        "avoid_patterns": TONE_MODIFIERS.get(tone, {}).get("avoid", []),
        "emoji_usage": "none" if tone in ["formal", "technical"] else "minimal",
        "language_complexity": "high" if tone == "technical" else "medium"
    }
    usage_log(api_key, "genome", "build_profile")
    success = genome_save(api_key, profile)
    if not success:
        return {"status": "error", "message": "failed to save profile", "layer": "GENOME"}
    return {"status": "saved", "profile": profile, "layer": "GENOME"}


def genome_get_profile(api_key):
    log_layer("genome", "get_profile", api_key)
    profile = genome_get(api_key)
    if not profile:
        return {"status": "no_profile", "message": "no personality profile set", "layer": "GENOME"}
    return {"status": "found", "profile": profile, "layer": "GENOME"}


def genome_inject_personality(response, api_key):
    log_layer("genome", "inject", api_key)
    if not response:
        return {"status": "error", "message": "response required", "layer": "GENOME"}
    usage_log(api_key, "genome", "inject")
    profile = genome_get(api_key)
    if not profile:
        return {"status": "success", "response": response, "note": "no profile - default used", "layer": "GENOME"}
    modified = response
    avoid_words = profile.get("avoid_words", [])
    for word in avoid_words:
        modified = modified.replace(word, "")
        modified = modified.replace(word.capitalize(), "")
    modified = re.sub(r' +', ' ', modified).strip()
    return {"status": "success", "original": response, "response": modified, "personality_applied": profile.get("tone", "professional"), "layer": "GENOME"}


def genome_generate_prompt(api_key):
    log_layer("genome", "prompt", api_key)
    profile = genome_get(api_key)
    if not profile:
        return {"system_prompt": "You are a helpful AI assistant.", "layer": "GENOME"}
    traits = ", ".join(profile.get("personality_traits", ["helpful"]))
    tone = profile.get("tone", "professional")
    business = profile.get("business_name", "this business")
    style = profile.get("communication_style", "Be helpful and clear")
    avoid = profile.get("avoid_patterns", [])
    avoid_str = f"Avoid: {', '.join(avoid[:5])}" if avoid else ""
    prompt = f"You are the AI assistant for {business}.\nPersonality: {traits}.\nTone: {tone}.\nStyle: {style}.\n{avoid_str}\nAlways represent {business} professionally."
    return {"system_prompt": prompt, "profile_name": business, "layer": "GENOME"}


def nexus_connect_source(source_type, source_url, api_key, name="", refresh_minutes=60):
    log_layer("nexus", "connect_source", api_key)
    if source_type not in SUPPORTED_SOURCE_TYPES:
        return {"status": "error", "message": f"Unsupported type. Supported: {SUPPORTED_SOURCE_TYPES}", "layer": "NEXUS"}
    valid, err = validate_text(source_url, max_length=2000, field_name="source_url")
    if not valid:
        return {"status": "error", "message": err, "layer": "NEXUS"}
    config = {"url": sanitize_text(source_url), "name": sanitize_text(name)[:100], "refresh_minutes": min(max(refresh_minutes, 5), 1440), "source_type": source_type}
    usage_log(api_key, "nexus", "connect_source")
    success = nexus_source_save(api_key, source_type, config)
    if not success:
        return {"status": "error", "message": "failed to save source", "layer": "NEXUS"}
    return {"status": "connected", "source_type": source_type, "name": name or source_url[:50], "layer": "NEXUS"}


def nexus_fetch_url(url, api_key):
    log_layer("nexus", "fetch_url", api_key)
    valid, err = validate_text(url, max_length=2000, field_name="url")
    if not valid:
        return {"status": "error", "message": err, "layer": "NEXUS"}
    if not url.startswith(("http://", "https://")):
        return {"status": "error", "message": "url must start with http or https", "layer": "NEXUS"}
    usage_log(api_key, "nexus", "fetch_url")
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True, headers={"User-Agent": "KRONYX-NEXUS/1.0"})
        if response.status_code == 200:
            return {"status": "success", "url": url, "content": response.text[:5000], "content_length": len(response.text), "layer": "NEXUS"}
        return {"status": "error", "message": f"HTTP {response.status_code}", "layer": "NEXUS"}
    except httpx.TimeoutException:
        return {"status": "error", "message": "url request timed out", "layer": "NEXUS"}
    except Exception as e:
        log_error(str(e), api_key=api_key, context="nexus.fetch_url")
        return {"status": "error", "message": "failed to fetch url", "layer": "NEXUS"}


def nexus_add_knowledge(content, topic, api_key):
    log_layer("nexus", "add_knowledge", api_key)
    valid, err = validate_text(content, field_name="content")
    if not valid:
        return {"status": "error", "message": err, "layer": "NEXUS"}
    valid, err = validate_text(topic, max_length=200, field_name="topic")
    if not valid:
        return {"status": "error", "message": err, "layer": "NEXUS"}
    usage_log(api_key, "nexus", "add_knowledge")
    entry = f"[KNOWLEDGE:{sanitize_text(topic)}] {sanitize_text(content)}"
    result = memory_insert(entry, f"nexus_{topic[:20]}", api_key)
    if "error" in result:
        return {"status": "error", "message": "failed to store knowledge", "layer": "NEXUS"}
    return {"status": "stored", "topic": topic, "id": result.get("id", ""), "layer": "NEXUS"}


def nexus_get_knowledge(topic, api_key):
    log_layer("nexus", "get_knowledge", api_key)
    usage_log(api_key, "nexus", "get_knowledge")
    results = memory_search(f"KNOWLEDGE:{topic}", f"nexus_{topic[:20]}", api_key, 10)
    return {"status": "success", "topic": topic, "knowledge": results, "count": len(results), "layer": "NEXUS"}


def nexus_fuse_knowledge(query, api_key):
    log_layer("nexus", "fuse", api_key)
    usage_log(api_key, "nexus", "fuse")
    all_knowledge = memory_search(query, f"nexus_{query[:20]}", api_key, 5)
    fused = " | ".join([k.get("content", "") for k in all_knowledge if k.get("content")])
    return {"status": "success", "query": query, "fused_knowledge": fused[:3000] if fused else "no knowledge found", "sources_used": len(all_knowledge), "layer": "NEXUS"}


def nexus_get_sources(api_key):
    sources = nexus_sources_get(api_key)
    return {"sources": sources, "total": len(sources), "layer": "NEXUS"}


def echo_cross_check(response, previous_responses, api_key):
    log_layer("echo", "cross_check", api_key)
    if not response:
        return {"status": "error", "message": "response required", "layer": "ECHO"}
    valid, err = validate_text(response, max_length=100000, field_name="response")
    if not valid:
        return {"status": "error", "message": err, "layer": "ECHO"}
    usage_log(api_key, "echo", "cross_check")
    issues = []
    r_lower = response.lower()
    uncertainty_phrases = ["i think", "i believe", "maybe", "perhaps", "might be", "not sure", "possibly", "could be"]
    uncertainty_found = [p for p in uncertainty_phrases if p in r_lower]
    if uncertainty_found:
        issues.append({"type": "uncertainty", "detail": f"uncertainty phrases: {uncertainty_found[:3]}", "severity": "low"})
    hallucination_signals = ["as of my knowledge", "if i remember correctly", "i believe the date", "the current price is"]
    hallucination_found = [h for h in hallucination_signals if h in r_lower]
    if hallucination_found:
        issues.append({"type": "potential_hallucination", "detail": "possible hallucination signals", "severity": "medium"})
    contradiction_pairs = [("yes", "no"), ("true", "false"), ("always", "never"), ("possible", "impossible"), ("available", "unavailable"), ("open", "closed")]
    for word_a, word_b in contradiction_pairs:
        if word_a in r_lower and word_b in r_lower:
            issues.append({"type": "internal_contradiction", "detail": f"may contradict itself ({word_a}/{word_b})", "severity": "high"})
    historical_contradictions = []
    for prev in (previous_responses or [])[-5:]:
        if isinstance(prev, str):
            prev_lower = prev.lower()
            for word_a, word_b in contradiction_pairs:
                if word_a in r_lower and word_b in prev_lower:
                    historical_contradictions.append({"type": "historical_contradiction", "detail": f"contradicts previous response", "severity": "high"})
                    break
    all_issues = issues + historical_contradictions
    has_critical = any(i["severity"] == "high" for i in all_issues)
    score = 100
    for issue in all_issues:
        if issue["severity"] == "high":
            score -= 30
        elif issue["severity"] == "medium":
            score -= 15
        else:
            score -= 5
    score = max(0, score)
    return {"status": "checked", "is_consistent": not has_critical, "consistency_score": score, "issues_found": len(all_issues), "issues": all_issues, "recommendation": "review_before_sending" if has_critical else "safe_to_send", "layer": "ECHO"}


def echo_verify_factual(statement, context, api_key):
    log_layer("echo", "verify_factual", api_key)
    if not statement or not context:
        return {"status": "error", "message": "statement and context required", "layer": "ECHO"}
    usage_log(api_key, "echo", "verify_factual")
    s_lower = statement.lower()
    c_lower = context.lower()
    key_terms = [w for w in s_lower.split() if len(w) > 4]
    matches = sum(1 for term in key_terms if term in c_lower)
    alignment = round((matches / max(len(key_terms), 1)) * 100)
    return {"status": "verified", "alignment_score": alignment, "aligned": alignment > 30, "key_terms_checked": len(key_terms), "terms_found": matches, "layer": "ECHO"}


def lens_analyze(message, user_id, api_key, history=None):
    log_layer("lens", "analyze", api_key)
    if not message:
        return {"status": "error", "message": "message required", "layer": "LENS"}
    valid, err = validate_text(message, field_name="message")
    if not valid:
        return {"status": "error", "message": err, "layer": "LENS"}
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "LENS"}
    usage_log(api_key, "lens", "analyze")
    message_clean = sanitize_text(message)
    m_lower = message_clean.lower()
    from datetime import datetime
    hour = datetime.utcnow().hour
    time_contexts = {(0, 6): "late_night", (6, 12): "morning", (12, 17): "afternoon", (17, 21): "evening", (21, 24): "night"}
    time_context = "day"
    for (start, end), ctx in time_contexts.items():
        if start <= hour < end:
            time_context = ctx
            break
    domain_signals = {
        "medical": ["doctor", "health", "medicine", "symptom", "treatment", "hospital", "pain"],
        "legal": ["law", "contract", "lawyer", "legal", "rights", "court", "sue"],
        "financial": ["money", "investment", "bank", "loan", "tax", "budget", "profit"],
        "technical": ["code", "programming", "software", "bug", "function", "api", "system"],
        "business": ["business", "company", "customer", "sales", "marketing", "product"],
        "personal": ["personal", "family", "relationship", "life", "myself", "feel"]
    }
    detected_domain = "general"
    domain_scores = {}
    for domain, signals in domain_signals.items():
        score = sum(1 for s in signals if s in m_lower)
        if score > 0:
            domain_scores[domain] = score
    if domain_scores:
        detected_domain = max(domain_scores, key=domain_scores.get)
    complexity_signals = {
        "expert": ["specifically", "technically", "implementation", "methodology", "framework"],
        "intermediate": ["how to", "configure", "setup", "manage", "improve"],
        "beginner": ["what is", "explain", "simple", "basic", "help me understand"]
    }
    user_level = "intermediate"
    for level, signals in complexity_signals.items():
        if any(s in m_lower for s in signals):
            user_level = level
            break
    word_count = len(message_clean.split())
    is_question = message_clean.strip().endswith("?") or any(m_lower.startswith(w) for w in ["what", "how", "why", "when", "where", "who", "which", "can", "is"])
    positive_words = ["please", "thank", "help", "good", "great", "love", "like"]
    negative_words = ["problem", "issue", "wrong", "broken", "hate", "terrible", "bad", "error"]
    pos = sum(1 for w in positive_words if w in m_lower)
    neg = sum(1 for w in negative_words if w in m_lower)
    sentiment = "neutral"
    if pos > neg:
        sentiment = "positive"
    elif neg > pos:
        sentiment = "negative"
    interaction_count = len(history) if history else 0
    user_familiarity = "new" if interaction_count < 5 else "returning" if interaction_count < 20 else "loyal"
    context = {"time_context": time_context, "detected_domain": detected_domain, "user_expertise_level": user_level, "is_question": is_question, "sentiment": sentiment, "word_count": word_count, "user_familiarity": user_familiarity}
    params = {
        "use_simple_language": user_level == "beginner",
        "be_technical": user_level == "expert",
        "be_empathetic": sentiment == "negative",
        "be_brief": word_count < 10,
        "be_detailed": word_count > 30,
        "greet_new_user": user_familiarity == "new"
    }
    instructions = []
    if params["use_simple_language"]:
        instructions.append("Use very simple language")
    if params["be_technical"]:
        instructions.append("Use technical terminology")
    if params["be_empathetic"]:
        instructions.append("Be empathetic and understanding")
    if params["be_brief"]:
        instructions.append("Keep response concise")
    if params["be_detailed"]:
        instructions.append("Provide comprehensive response")
    if params["greet_new_user"]:
        instructions.append("Welcome them warmly")
    context_prompt = f"Context: {detected_domain} domain, {user_level} user, {sentiment} sentiment. Instructions: {'. '.join(instructions)}." if instructions else ""
    return {"status": "success", "context": context, "response_params": params, "context_prompt": context_prompt, "context_summary": f"{user_familiarity} {user_level} user in {detected_domain} domain, {sentiment} sentiment", "layer": "LENS"}


def lens_build_context_prompt(message, user_id, api_key):
    log_layer("lens", "build_prompt", api_key)
    analysis = lens_analyze(message, user_id, api_key)
    if analysis.get("status") != "success":
        return {"context_prompt": "", "layer": "LENS"}
    return {"context_prompt": analysis.get("context_prompt", ""), "context": analysis.get("context", {}), "layer": "LENS"}


def prima_process(text, api_key):
    log_layer("prima", "process", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "PRIMA"}
    valid, err = validate_text(text, field_name="text")
    if not valid:
        return {"status": "error", "message": err, "layer": "PRIMA"}
    usage_log(api_key, "prima", "process")
    text_clean = sanitize_text(text)
    t_lower = text_clean.lower()
    detected = {}
    relational_weights = {"containment": 0.8, "causation": 0.9, "opposition": 0.7, "sequence": 0.6, "similarity": 0.5, "intensity": 0.4, "uncertainty": 0.3, "negation": 0.8}
    for structure, signals in CONCEPTUAL_STRUCTURES.items():
        count = sum(1 for s in signals if s in t_lower)
        if count > 0:
            detected[structure] = {"count": count, "weight": relational_weights.get(structure, 0.5), "significance": count * relational_weights.get(structure, 0.5)}
    dominant = max(detected.items(), key=lambda x: x[1]["significance"])[0] if detected else None
    semantic_density = len(set(t_lower.split())) / max(len(t_lower.split()), 1)
    insights_map = {
        "causation": "Communication is about cause and effect relationships",
        "opposition": "Communication contains tension between opposing forces",
        "containment": "Communication deals with boundaries and inclusion",
        "sequence": "Communication describes a temporal or logical progression",
        "negation": "Communication is defined by what is absent or denied",
        "uncertainty": "Communication operates in a space of possibility"
    }
    insight = insights_map.get(dominant, "Complex multi-layered communication structure") if dominant else "Surface level symbolic communication"
    return {"status": "success", "dominant_structure": dominant, "structural_layers": list(detected.keys()), "complexity_score": len(detected) * 10, "semantic_density": round(semantic_density, 3), "pre_linguistic_insight": insight, "processing_depth": "pre_linguistic", "layer": "PRIMA"}
