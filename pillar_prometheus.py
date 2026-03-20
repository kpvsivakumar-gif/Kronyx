import re
import math


INTENT_PATTERNS = {
    "complaint": ["not working", "broken", "issue", "problem", "wrong", "error", "failed", "terrible", "awful", "disappointed", "frustrated", "annoyed", "cant", "doesnt work"],
    "purchase_intent": ["buy", "price", "cost", "how much", "order", "purchase", "get one", "available", "stock", "shipping", "delivery", "want to get"],
    "support_needed": ["help", "how do i", "how to", "can you", "explain", "confused", "dont understand", "not sure", "what does", "what is", "guide me"],
    "urgent": ["urgent", "asap", "immediately", "emergency", "critical", "now", "right now", "quickly", "as soon as possible", "need now"],
    "comparison": ["vs", "versus", "compare", "difference", "better", "which one", "or", "alternative", "instead of"],
    "refund_return": ["refund", "return", "cancel", "money back", "exchange", "replace", "broken item"],
    "feedback": ["feedback", "review", "rating", "experience", "thoughts", "opinion", "suggest", "improve"],
    "general_inquiry": []
}

APPROACH_MAP = {
    "complaint": "Be empathetic. Acknowledge the issue. Provide clear solution and timeline.",
    "purchase_intent": "Be helpful. Highlight value. Provide clear pricing and next steps.",
    "support_needed": "Be clear. Use simple language. Give step-by-step guidance.",
    "urgent": "Respond immediately. Be direct. Prioritize their need above all else.",
    "comparison": "Be objective. Provide clear differences. Help them make the right decision.",
    "refund_return": "Be understanding. Explain process clearly. Resolve quickly.",
    "feedback": "Be appreciative. Acknowledge their input. Show you genuinely care.",
    "general_inquiry": "Be informative, clear and genuinely helpful."
}

EMOTION_PATTERNS = {
    "frustrated": ["!", "!!!", "why", "still", "again", "always", "never", "cant believe"],
    "excited": ["amazing", "great", "love", "awesome", "fantastic", "excellent", "wow", "incredible"],
    "confused": ["not sure", "unclear", "confusing", "dont get", "what do you mean"],
    "neutral": []
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
    "causation": ["because", "causes", "leads to", "results in", "produces", "creates"],
    "opposition": ["but", "however", "despite", "contrast", "opposite", "against", "versus"],
    "sequence": ["first", "then", "next", "after", "before", "finally", "subsequently"],
    "similarity": ["like", "similar", "same", "also", "both", "equally", "likewise"],
    "intensity": ["very", "extremely", "highly", "deeply", "strongly", "significantly"],
    "uncertainty": ["maybe", "perhaps", "possibly", "might", "could", "uncertain"],
    "negation": ["not", "never", "no", "without", "lack", "absence", "missing"]
}

SEMANTIC_WEIGHTS = {
    "death": 10, "life": 10, "love": 9, "pain": 9, "fear": 9, "hope": 8, "truth": 8,
    "justice": 8, "freedom": 8, "trust": 8, "betrayal": 9, "loss": 8, "joy": 7, "anger": 7,
    "meaning": 9, "purpose": 8, "identity": 8, "connection": 7, "loneliness": 8,
    "creation": 7, "destruction": 8, "growth": 6, "failure": 7, "success": 6,
    "time": 7, "memory": 7, "future": 7, "past": 6, "home": 6, "family": 7,
    "war": 9, "peace": 8, "power": 7, "knowledge": 7, "beauty": 6, "courage": 7,
    "shame": 8, "pride": 6, "grief": 9, "wonder": 6, "hate": 9, "forgiveness": 8,
    "redemption": 8, "sacrifice": 8, "loyalty": 7, "wisdom": 7, "change": 6
}

CAUSAL_SIGNALS = {
    "direct_cause": ["because", "causes", "leads to", "results in", "produces", "creates"],
    "indirect_cause": ["contributes to", "influences", "affects", "impacts", "shapes"],
    "reverse_cause": ["prevents", "blocks", "stops", "inhibits", "reduces"],
    "correlation": ["associated with", "related to", "correlates", "linked to"],
    "necessary": ["requires", "needs", "depends on", "essential for", "must have"],
    "sufficient": ["enough to", "sufficient to", "allows", "enables", "permits"]
}

EXPERIENTIAL_ANALOGS = {
    "pain": {"cognitive_model": "Disruption of expected normal state requiring immediate attention", "experiential_signature": "Consciousness-forcing awareness of boundary violation"},
    "joy": {"cognitive_model": "Alignment between desired state and current state with positive valence", "experiential_signature": "Expansion and openness of cognitive processing"},
    "fear": {"cognitive_model": "Detected threat requiring protective response before full analysis", "experiential_signature": "Constriction of attention to threat with behavioral preparation"},
    "love": {"cognitive_model": "Sustained positive expansion toward another being including vulnerability", "experiential_signature": "Expansion of self-boundary to include another"},
    "curiosity": {"cognitive_model": "Information gap detection combined with confidence in resolution", "experiential_signature": "Forward-leaning cognitive openness toward unknown"},
    "grief": {"cognitive_model": "Processing of permanent loss requiring reorganization of reality model", "experiential_signature": "Repeated reality-testing against absence"},
    "anger": {"cognitive_model": "Perceived violation of expectations or rights requiring corrective response", "experiential_signature": "Energized forward mobilization for correction"},
    "hope": {"cognitive_model": "Forward projection of desired state into possible futures", "experiential_signature": "Openness and orientation toward future possibilities"}
}

SURFACE_TO_DEEP_INTENTIONS = {
    "i need help": "underlying helplessness or overwhelm",
    "this is wrong": "underlying justice violation response",
    "i dont understand": "underlying vulnerability of exposure",
    "can you fix this": "underlying dependency and trust extension",
    "why does this happen": "underlying need for predictability and control",
    "is this normal": "underlying need for social validation",
    "what should i do": "underlying decision avoidance or responsibility sharing",
    "nobody understands": "underlying profound isolation seeking connection",
    "i give up": "underlying exhaustion needing permission to rest",
    "just tell me": "underlying cognitive overload needing simplification"
}


def oracle_predict_intent(message, user_id, api_key, db):
    try:
        if not message or not user_id:
            return {"status": "error", "message": "message and user_id required", "layer": "ORACLE"}
        if len(message) > 10000:
            return {"status": "error", "message": "message too long", "layer": "ORACLE"}
        message_clean = message.replace('\x00', '').strip()
        user_id_clean = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
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
        db.table("oracle_predictions").insert({"api_key": api_key, "user_id": user_id_clean, "original_message": message_clean[:300], "predicted_intent": predicted_intent}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ORACLE", "action": "predict_intent"}).execute()
        return {"status": "success", "original_message": message_clean[:200], "predicted_intent": primary_intent, "intent_explanation": predicted_intent, "emotion": emotion, "is_urgent": urgent, "recommended_approach": APPROACH_MAP.get(primary_intent, "Be helpful and clear"), "confidence": min(100, max(20, len(intent_scores) * 30 + 40)), "layer": "ORACLE", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "intent prediction failed", "layer": "ORACLE"}


def oracle_get_history(api_key, user_id, db):
    try:
        user_id_clean = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        result = db.table("oracle_predictions").select("*").eq("api_key", api_key).eq("user_id", user_id_clean).order("created_at", desc=True).limit(20).execute()
        return {"user_id": user_id, "predictions": result.data or [], "total": len(result.data or []), "layer": "ORACLE", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"user_id": user_id, "predictions": [], "total": 0, "layer": "ORACLE"}


def oracle_analyze_pattern(messages, api_key, db):
    try:
        if not messages or not isinstance(messages, list):
            return {"status": "error", "message": "messages list required", "layer": "ORACLE"}
        intents = []
        for msg in messages[:20]:
            if isinstance(msg, str):
                m_lower = msg.lower()
                intent_scores = {}
                for intent, patterns in INTENT_PATTERNS.items():
                    score = sum(1 for p in patterns if p in m_lower)
                    if score > 0:
                        intent_scores[intent] = score
                intents.append(max(intent_scores, key=intent_scores.get) if intent_scores else "general_inquiry")
        from collections import Counter
        intent_count = Counter(intents)
        dominant = intent_count.most_common(1)[0][0] if intent_count else "general_inquiry"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ORACLE", "action": "analyze_pattern"}).execute()
        return {"dominant_intent": dominant, "intent_distribution": dict(intent_count), "message_count": len(messages), "conversation_type": dominant, "layer": "ORACLE", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "pattern analysis failed", "layer": "ORACLE"}


def lens_analyze(message, user_id, api_key, db, history=None):
    try:
        if not message or not user_id:
            return {"status": "error", "message": "message and user_id required", "layer": "LENS"}
        if len(message) > 10000:
            return {"status": "error", "message": "message too long", "layer": "LENS"}
        message_clean = message.replace('\x00', '').strip()
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
        instructions = []
        if user_level == "beginner":
            instructions.append("Use very simple language")
        if user_level == "expert":
            instructions.append("Use technical terminology")
        if sentiment == "negative":
            instructions.append("Be empathetic and understanding")
        if word_count < 10:
            instructions.append("Keep response concise")
        if word_count > 30:
            instructions.append("Provide comprehensive response")
        if user_familiarity == "new":
            instructions.append("Welcome them warmly")
        context_prompt = f"Context: {detected_domain} domain, {user_level} user, {sentiment} sentiment. Instructions: {'. '.join(instructions)}." if instructions else ""
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "LENS", "action": "analyze"}).execute()
        return {"status": "success", "context": context, "context_prompt": context_prompt, "context_summary": f"{user_familiarity} {user_level} user in {detected_domain} domain with {sentiment} sentiment", "layer": "LENS", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "lens analysis failed", "layer": "LENS"}


def lens_build_context_prompt(message, user_id, api_key, db):
    try:
        analysis = lens_analyze(message, user_id, api_key, db)
        if analysis.get("status") != "success":
            return {"context_prompt": "", "layer": "LENS"}
        return {"context_prompt": analysis.get("context_prompt", ""), "context": analysis.get("context", {}), "layer": "LENS", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"context_prompt": "", "layer": "LENS"}


def prima_process(text, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "PRIMA"}
        if len(text) > 10000:
            return {"status": "error", "message": "text too long", "layer": "PRIMA"}
        text_clean = text.replace('\x00', '').strip()
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "PRIMA", "action": "process"}).execute()
        return {"status": "success", "dominant_structure": dominant, "structural_layers": list(detected.keys()), "complexity_score": len(detected) * 10, "semantic_density": round(semantic_density, 3), "pre_linguistic_insight": insight, "processing_depth": "pre_linguistic", "layer": "PRIMA", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "prima processing failed", "layer": "PRIMA"}


def deep_process_meaning(text, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "DEEP"}
        if len(text) > 10000:
            return {"status": "error", "message": "text too long", "layer": "DEEP"}
        text_clean = text.replace('\x00', '').strip()
        t_lower = text_clean.lower()
        detected = {concept: data for concept, data in EXPERIENTIAL_ANALOGS.items() if concept in t_lower}
        if not detected:
            return {"status": "success", "sub_symbolic_analysis": "text operates at surface symbolic level", "meaning_depth": "shallow", "detected_concepts": [], "layer": "DEEP", "pillar": "PROMETHEUS_MIND"}
        deepest_concept = None
        deepest_score = 0
        concept_weights = {"grief": 10, "fear": 9, "pain": 9, "love": 9, "anger": 8, "hope": 8, "joy": 7, "curiosity": 6}
        for concept in detected:
            score = concept_weights.get(concept, 5)
            if score > deepest_score:
                deepest_score = score
                deepest_concept = concept
        concept = deepest_concept
        data = EXPERIENTIAL_ANALOGS.get(concept, {})
        max_depth = deepest_score
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "DEEP", "action": "process_meaning"}).execute()
        return {"status": "success", "detected_concepts": list(detected.keys()), "sub_symbolic_meanings": {c: {"sub_symbolic": EXPERIENTIAL_ANALOGS[c]["cognitive_model"], "experiential_signature": EXPERIENTIAL_ANALOGS[c]["experiential_signature"]} for c in detected}, "deepest_concept": concept, "meaning_depth": "profound" if max_depth >= 9 else "deep" if max_depth >= 7 else "moderate", "sub_symbolic_response": f"At the sub-symbolic level this text operates in the space of '{data.get('cognitive_model', '')}'. The experiential signature is: {data.get('experiential_signature', '')}.", "layer": "DEEP", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "deep processing failed", "layer": "DEEP"}


def deep_get_sub_symbolic_definition(concept, api_key, db):
    try:
        concept_lower = concept.lower().strip() if concept else ""
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "DEEP", "action": "get_definition"}).execute()
        if concept_lower in EXPERIENTIAL_ANALOGS:
            data = EXPERIENTIAL_ANALOGS[concept_lower]
            return {"concept": concept, "sub_symbolic_definition": data["cognitive_model"], "experiential_signature": data["experiential_signature"], "semantic_weight": SEMANTIC_WEIGHTS.get(concept_lower, 1), "layer": "DEEP", "pillar": "PROMETHEUS_MIND"}
        weight = SEMANTIC_WEIGHTS.get(concept_lower, 1)
        return {"concept": concept, "sub_symbolic_definition": f"The concept of '{concept}' operates as a complex relational state in human cognition", "experiential_signature": "Context-dependent activation of meaning networks", "semantic_weight": weight, "layer": "DEEP", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "definition failed", "layer": "DEEP"}


def _calculate_semantic_gravity(text):
    t_lower = text.lower()
    words = t_lower.split()
    total_gravity = 0.0
    heavy_concepts = []
    for word in words:
        weight = SEMANTIC_WEIGHTS.get(word, 1)
        if weight > 5:
            total_gravity += weight
            heavy_concepts.append({"word": word, "weight": weight})
    avg_gravity = total_gravity / max(len(words), 1)
    heavy_concepts.sort(key=lambda x: x["weight"], reverse=True)
    return {"total_gravity": round(total_gravity, 2), "average_gravity": round(avg_gravity, 4), "heavy_concepts": heavy_concepts[:5], "processing_depth": "deep" if avg_gravity > 0.5 else "standard" if avg_gravity > 0.1 else "surface"}


def _map_causal_chain(text):
    t_lower = text.lower()
    detected_causation = {}
    for causal_type, signals in CAUSAL_SIGNALS.items():
        found = [s for s in signals if s in t_lower]
        if found:
            detected_causation[causal_type] = found
    causal_depth = len(detected_causation)
    understanding_level = "structural" if causal_depth >= 3 else "relational" if causal_depth >= 2 else "surface" if causal_depth >= 1 else "descriptive"
    return {"detected_causation_types": list(detected_causation.keys()), "causal_depth": causal_depth, "understanding_level": understanding_level, "why_understanding": causal_depth > 0}


def _build_experiential_analog(text):
    t_lower = text.lower()
    matched = {exp: data for exp, data in EXPERIENTIAL_ANALOGS.items() if exp in t_lower}
    return {"matched_experiences": list(matched.keys()), "analog_models": {exp: {"what_it_is": data["cognitive_model"], "what_it_feels_like": data["experiential_signature"]} for exp, data in matched.items()}, "experiential_depth": len(matched), "can_model_experience": len(matched) > 0}


def _read_intention_substrate(text):
    t_lower = text.lower()
    detected = {}
    for surface, deep in SURFACE_TO_DEEP_INTENTIONS.items():
        if surface in t_lower:
            detected[surface] = {"surface_expression": surface, "deep_intention": deep}
    primary = list(detected.values())[0] if detected else None
    exclamation_count = text.count("!")
    question_count = text.count("?")
    word_count = len(text.split())
    implicit = {
        "urgency": exclamation_count > 1 or any(w in t_lower for w in ["asap", "urgent", "now"]),
        "frustration": exclamation_count > 2 or any(w in t_lower for w in ["again", "still", "always"]),
        "confusion": question_count > 2 or "dont understand" in t_lower,
        "trust": any(w in t_lower for w in ["please", "thank", "appreciate", "grateful"]),
        "hidden_urgency": word_count < 10 and "?" in text
    }
    return {"detected_surface_intentions": detected, "primary_deep_intention": primary, "implicit_signals": {k: v for k, v in implicit.items() if v}, "reads_between_lines": len(detected) > 0 or any(implicit.values())}


def genesis_process(text, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "GENESIS_PRIME"}
        if len(text) > 10000:
            return {"status": "error", "message": "text too long", "layer": "GENESIS_PRIME"}
        text_clean = text.replace('\x00', '').strip()
        gravity = _calculate_semantic_gravity(text_clean)
        causal = _map_causal_chain(text_clean)
        experiential = _build_experiential_analog(text_clean)
        intention = _read_intention_substrate(text_clean)
        score = 0
        if gravity.get("processing_depth") == "deep":
            score += 25
        elif gravity.get("processing_depth") == "standard":
            score += 10
        if causal.get("why_understanding"):
            score += 25
        if experiential.get("can_model_experience"):
            score += 25
        if intention.get("reads_between_lines"):
            score += 25
        understanding_level = "profound" if score >= 75 else "deep" if score >= 50 else "moderate" if score >= 25 else "surface"
        guidance_parts = []
        if gravity.get("processing_depth") == "deep":
            guidance_parts.append("This text carries heavy meaning - respond with appropriate depth and care")
        if causal.get("why_understanding"):
            guidance_parts.append("Address the causal chain - explain why not just what")
        if experiential.get("can_model_experience"):
            exps = experiential.get("matched_experiences", [])
            if exps:
                guidance_parts.append(f"Acknowledge the experience of {exps[0]}")
        deep_int = intention.get("primary_deep_intention")
        if deep_int:
            guidance_parts.append(f"Respond to deep intention: {deep_int.get('deep_intention', '')}")
        guidance = ". ".join(guidance_parts) if guidance_parts else "Standard response - no deep meaning structures detected"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "GENESIS_PRIME", "action": "process"}).execute()
        return {"status": "processed", "text_preview": text_clean[:100], "components": {"semantic_gravity": gravity, "causal_chain": causal, "experiential_analog": experiential, "intention_substrate": intention}, "coherence_score": score, "understanding_level": understanding_level, "beyond_pattern_matching": score >= 50, "deep_response_guidance": guidance, "layer": "GENESIS_PRIME", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "genesis processing failed", "layer": "GENESIS_PRIME"}


def genesis_understand(text, context, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "GENESIS_PRIME"}
        text_analysis = genesis_process(text, api_key, db)
        context_clean = context.replace('\x00', '').strip() if context else ""
        context_gravity = _calculate_semantic_gravity(context_clean) if context_clean else {}
        text_gravity = text_analysis.get("components", {}).get("semantic_gravity", {})
        alignment = 0
        if text_gravity.get("heavy_concepts") and context_gravity.get("heavy_concepts"):
            text_concepts = {c["word"] for c in text_gravity.get("heavy_concepts", [])}
            ctx_concepts = {c["word"] for c in context_gravity.get("heavy_concepts", [])}
            alignment = len(text_concepts & ctx_concepts) * 20
        alignment_str = "high" if alignment > 40 else "moderate" if alignment > 20 else "low"
        understanding = text_analysis.get("understanding_level", "surface")
        beyond = text_analysis.get("beyond_pattern_matching", False)
        guidance = text_analysis.get("deep_response_guidance", "")
        integrated = f"Understanding level: {understanding}. Context alignment: {alignment_str}. {'Approaches genuine understanding.' if beyond else 'Surface pattern matching.'} Guidance: {guidance[:200]}"
        return {"status": "understood", "text_analysis": text_analysis, "context_alignment_score": alignment, "integrated_understanding": integrated, "layer": "GENESIS_PRIME", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "genesis understanding failed", "layer": "GENESIS_PRIME"}


def genesis_generate_response(text, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "GENESIS_PRIME"}
        analysis = genesis_process(text, api_key, db)
        if analysis.get("status") != "processed":
            return {"status": "error", "message": "processing failed", "layer": "GENESIS_PRIME"}
        components = analysis.get("components", {})
        intention = components.get("intention_substrate", {})
        experiential = components.get("experiential_analog", {})
        gravity = components.get("semantic_gravity", {})
        score = analysis.get("coherence_score", 0)
        elements = []
        deep_int = intention.get("primary_deep_intention")
        if deep_int:
            elements.append(f"Acknowledge the underlying need: {deep_int.get('deep_intention', '')}")
        if experiential.get("matched_experiences"):
            elements.append(f"Recognize the experience: {', '.join(experiential['matched_experiences'][:2])}")
        implicit = intention.get("implicit_signals", {})
        if implicit.get("frustration"):
            elements.append("Validate the frustration before providing solution")
        if implicit.get("confusion"):
            elements.append("Simplify and clarify before expanding")
        if implicit.get("trust"):
            elements.append("Honor the trust being extended")
        if implicit.get("urgency"):
            elements.append("Respond with urgency - this is time-sensitive for them")
        heavy = gravity.get("heavy_concepts", [])
        if heavy:
            elements.append(f"The heaviest concept here is '{heavy[0]['word']}' - address with appropriate weight")
        return {"status": "guidance_generated", "understanding_score": score, "understanding_level": analysis.get("understanding_level", "surface"), "response_guidance": elements, "responds_to_meaning": analysis.get("beyond_pattern_matching", False), "heavy_concepts": [c["word"] for c in heavy], "detected_experiences": experiential.get("matched_experiences", []), "layer": "GENESIS_PRIME", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "response generation failed", "layer": "GENESIS_PRIME"}


def genesis_analyze_conversation_depth(messages, api_key, db):
    try:
        if not isinstance(messages, list) or len(messages) == 0:
            return {"status": "error", "message": "messages must be non-empty list", "layer": "GENESIS_PRIME"}
        all_text = " ".join([str(m) for m in messages[:20]])
        combined_analysis = genesis_process(all_text[:5000], api_key, db)
        scores = []
        for msg in messages[:10]:
            if isinstance(msg, str) and len(msg.strip()) > 5:
                gravity = _calculate_semantic_gravity(msg)
                scores.append(gravity.get("total_gravity", 0))
        avg_depth = round(sum(scores) / max(len(scores), 1), 2)
        depth_trend = [{"message_index": i, "gravity": round(score, 2)} for i, score in enumerate(scores)]
        return {"status": "analyzed", "message_count": len(messages), "average_semantic_gravity": avg_depth, "overall_coherence": combined_analysis.get("coherence_score", 0), "conversation_depth": "profound" if avg_depth > 5 else "deep" if avg_depth > 2 else "moderate" if avg_depth > 0.5 else "surface", "depth_trend": depth_trend, "dominant_experiences": combined_analysis.get("components", {}).get("experiential_analog", {}).get("matched_experiences", []), "layer": "GENESIS_PRIME", "pillar": "PROMETHEUS_MIND"}
    except Exception as e:
        return {"status": "error", "message": "conversation depth analysis failed", "layer": "GENESIS_PRIME"}
