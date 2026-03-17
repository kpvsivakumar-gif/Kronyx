from database import usage_log
from validators import validate_text, sanitize_text
from logger import log_layer

SEMANTIC_WEIGHTS = {
    "death": 10, "life": 10, "love": 9, "pain": 9, "fear": 9, "hope": 8, "truth": 8,
    "justice": 8, "freedom": 8, "trust": 8, "betrayal": 9, "loss": 8, "joy": 7, "anger": 7,
    "meaning": 9, "purpose": 8, "identity": 8, "connection": 7, "loneliness": 8,
    "creation": 7, "destruction": 8, "growth": 6, "failure": 7, "success": 6,
    "time": 7, "memory": 7, "future": 7, "past": 6, "home": 6, "family": 7,
    "war": 9, "peace": 8, "power": 7, "knowledge": 7, "ignorance": 7, "beauty": 6,
    "courage": 7, "shame": 8, "pride": 6, "grief": 9, "joy": 7, "wonder": 6,
    "hate": 9, "forgiveness": 8, "redemption": 8, "sacrifice": 8, "betrayal": 9,
    "loyalty": 7, "wisdom": 7, "ignorance": 7, "change": 6, "permanence": 7
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
    "pride": {"cognitive_model": "Recognition of alignment between action and values by self and others", "experiential_signature": "Upward expansion of self-assessment"},
    "shame": {"cognitive_model": "Recognition of gap between actual and ideal self with social visibility", "experiential_signature": "Downward contraction with hiding impulse"},
    "anger": {"cognitive_model": "Perceived violation of expectations or rights requiring corrective response", "experiential_signature": "Energized forward mobilization for correction"},
    "hope": {"cognitive_model": "Forward projection of desired state into possible futures", "experiential_signature": "Openness and orientation toward future possibilities"}
}

SURFACE_TO_DEEP_INTENTIONS = {
    "i need help": "underlying helplessness or overwhelm",
    "this is wrong": "underlying justice violation response",
    "i don't understand": "underlying vulnerability of exposure",
    "can you fix this": "underlying dependency and trust extension",
    "why does this happen": "underlying need for predictability and control",
    "is this normal": "underlying need for social validation",
    "what should i do": "underlying decision avoidance or responsibility sharing",
    "nobody understands": "underlying profound isolation seeking connection",
    "i give up": "underlying exhaustion needing permission to rest",
    "just tell me": "underlying cognitive overload needing simplification",
    "am i doing this right": "underlying insecurity seeking validation",
    "is there another way": "underlying dissatisfaction with current approach",
    "what if": "underlying exploratory thinking or anxiety about alternatives",
    "i tried everything": "underlying exhaustion and hopelessness",
    "it doesn't matter": "underlying resignation or hidden strong emotion"
}


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
    return {
        "total_gravity": round(total_gravity, 2),
        "average_gravity": round(avg_gravity, 4),
        "heavy_concepts": heavy_concepts[:5],
        "processing_depth": "deep" if avg_gravity > 0.5 else "standard" if avg_gravity > 0.1 else "surface"
    }


def _map_causal_chain(text):
    t_lower = text.lower()
    detected_causation = {}
    for causal_type, signals in CAUSAL_SIGNALS.items():
        found = [s for s in signals if s in t_lower]
        if found:
            detected_causation[causal_type] = found
    sentences = text.split(".")
    causal_chains = []
    for sentence in sentences[:10]:
        s_lower = sentence.lower()
        for causal_type, signals in CAUSAL_SIGNALS.items():
            if any(s in s_lower for s in signals):
                causal_chains.append({"sentence": sentence.strip()[:150], "causal_type": causal_type})
                break
    causal_depth = len(detected_causation)
    understanding_level = "structural" if causal_depth >= 3 else "relational" if causal_depth >= 2 else "surface" if causal_depth >= 1 else "descriptive"
    return {"detected_causation_types": list(detected_causation.keys()), "causal_chains": causal_chains[:5], "causal_depth": causal_depth, "understanding_level": understanding_level, "why_understanding": causal_depth > 0}


def _build_experiential_analog(text):
    t_lower = text.lower()
    matched = {exp: data for exp, data in EXPERIENTIAL_ANALOGS.items() if exp in t_lower}
    analog_understanding = {exp: {"what_it_is": data["cognitive_model"], "what_it_feels_like": data["experiential_signature"]} for exp, data in matched.items()}
    return {"matched_experiences": list(matched.keys()), "analog_models": analog_understanding, "experiential_depth": len(matched), "can_model_experience": len(matched) > 0}


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
        "confusion": question_count > 2 or "don't understand" in t_lower,
        "trust": any(w in t_lower for w in ["please", "thank", "appreciate", "grateful"]),
        "urgency_hidden": word_count < 10 and "?" in text
    }
    return {"detected_surface_intentions": detected, "primary_deep_intention": primary, "implicit_signals": {k: v for k, v in implicit.items() if v}, "reads_between_lines": len(detected) > 0 or any(implicit.values())}


def _build_coherence_model(all_components):
    gravity = all_components.get("semantic_gravity", {})
    causal = all_components.get("causal_chain", {})
    experiential = all_components.get("experiential_analog", {})
    intention = all_components.get("intention_substrate", {})
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
    return {"coherence_score": score, "understanding_level": understanding_level, "beyond_pattern_matching": score >= 50, "approaches_understanding": score >= 75}


def process(text, api_key):
    log_layer("genesis_prime", "process", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "GENESIS_PRIME"}
    valid, err = validate_text(text, field_name="text")
    if not valid:
        return {"status": "error", "message": err, "layer": "GENESIS_PRIME"}
    usage_log(api_key, "genesis_prime", "process")
    text_clean = sanitize_text(text)
    gravity = _calculate_semantic_gravity(text_clean)
    causal = _map_causal_chain(text_clean)
    experiential = _build_experiential_analog(text_clean)
    intention = _read_intention_substrate(text_clean)
    all_components = {"semantic_gravity": gravity, "causal_chain": causal, "experiential_analog": experiential, "intention_substrate": intention}
    coherence = _build_coherence_model(all_components)
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
    return {
        "status": "processed",
        "text_preview": text_clean[:100],
        "components": {"semantic_gravity": gravity, "causal_chain": causal, "experiential_analog": experiential, "intention_substrate": intention, "coherence_layer": coherence},
        "coherence_score": coherence["coherence_score"],
        "understanding_level": coherence["understanding_level"],
        "beyond_pattern_matching": coherence["beyond_pattern_matching"],
        "deep_response_guidance": guidance,
        "layer": "GENESIS_PRIME"
    }


def understand(text, context, api_key):
    log_layer("genesis_prime", "understand", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "GENESIS_PRIME"}
    usage_log(api_key, "genesis_prime", "understand")
    text_clean = sanitize_text(text)
    context_clean = sanitize_text(context) if context else ""
    text_analysis = process(text_clean, api_key)
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
    return {"status": "understood", "text_analysis": text_analysis, "context_alignment_score": alignment, "integrated_understanding": integrated, "layer": "GENESIS_PRIME"}


def generate_understanding_response(text, api_key):
    log_layer("genesis_prime", "generate_response", api_key)
    usage_log(api_key, "genesis_prime", "generate_response")
    analysis = process(text, api_key)
    if analysis.get("status") != "processed":
        return {"status": "error", "message": "processing failed", "layer": "GENESIS_PRIME"}
    components = analysis.get("components", {})
    intention = components.get("intention_substrate", {})
    experiential = components.get("experiential_analog", {})
    coherence = components.get("coherence_layer", {})
    gravity = components.get("semantic_gravity", {})
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
        elements.append(f"The heaviest concept here is '{heavy[0]['word']}' - address this with appropriate weight")
    return {
        "status": "guidance_generated",
        "understanding_score": coherence.get("coherence_score", 0),
        "understanding_level": coherence.get("understanding_level", "surface"),
        "response_guidance": elements,
        "responds_to_meaning": coherence.get("beyond_pattern_matching", False),
        "heavy_concepts": [c["word"] for c in heavy],
        "detected_experiences": experiential.get("matched_experiences", []),
        "layer": "GENESIS_PRIME"
    }


def get_semantic_weight(word, api_key):
    log_layer("genesis_prime", "semantic_weight", api_key)
    usage_log(api_key, "genesis_prime", "semantic_weight")
    weight = SEMANTIC_WEIGHTS.get(word.lower().strip(), 1)
    return {"word": word, "weight": weight, "significance": "very_high" if weight >= 9 else "high" if weight >= 7 else "medium" if weight >= 5 else "low", "layer": "GENESIS_PRIME"}


def analyze_conversation_depth(messages, api_key):
    log_layer("genesis_prime", "conversation_depth", api_key)
    if not isinstance(messages, list) or len(messages) == 0:
        return {"status": "error", "message": "messages must be non-empty list", "layer": "GENESIS_PRIME"}
    usage_log(api_key, "genesis_prime", "conversation_depth")
    all_text = " ".join([str(m) for m in messages[:20]])
    combined_analysis = process(all_text[:5000], api_key)
    scores = []
    for msg in messages[:10]:
        if isinstance(msg, str) and len(msg.strip()) > 5:
            gravity = _calculate_semantic_gravity(msg)
            scores.append(gravity.get("total_gravity", 0))
    avg_depth = round(sum(scores) / max(len(scores), 1), 2)
    depth_trend = []
    for i, score in enumerate(scores):
        depth_trend.append({"message_index": i, "gravity": round(score, 2)})
    return {
        "status": "analyzed",
        "message_count": len(messages),
        "average_semantic_gravity": avg_depth,
        "overall_coherence": combined_analysis.get("coherence_score", 0),
        "conversation_depth": "profound" if avg_depth > 5 else "deep" if avg_depth > 2 else "moderate" if avg_depth > 0.5 else "surface",
        "depth_trend": depth_trend,
        "dominant_experiences": combined_analysis.get("components", {}).get("experiential_analog", {}).get("matched_experiences", []),
        "layer": "GENESIS_PRIME"
    }
