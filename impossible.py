import math
import random
from database import usage_log
from validators import validate_text, sanitize_text
from logger import log_layer

UNIVERSAL_PATTERNS = {
    "branching": {"description": "A central source divides into multiple paths", "domains": ["biology:trees", "geology:rivers", "neuroscience:neurons", "business:org_charts", "technology:networks"], "signals": ["branch", "divide", "split", "fork", "tree", "network", "spread"]},
    "cycles": {"description": "Recurring patterns that return to their origin", "domains": ["astronomy:orbits", "biology:seasons", "economics:business_cycles", "psychology:habit_loops"], "signals": ["cycle", "repeat", "return", "loop", "periodic", "recurring", "rotate"]},
    "emergence": {"description": "Simple components create complex unexpected behavior", "domains": ["biology:consciousness", "economics:markets", "physics:thermodynamics", "sociology:culture"], "signals": ["emerge", "arise", "appear", "complex", "unexpected", "collective", "system"]},
    "compression": {"description": "Large complex things reduce to essential core", "domains": ["physics:black_holes", "mathematics:compression", "biology:DNA", "business:strategy"], "signals": ["compress", "reduce", "simplify", "distill", "core", "essential", "summary"]},
    "resonance": {"description": "Matching frequencies amplify each other", "domains": ["physics:sound", "psychology:rapport", "economics:markets", "relationships:communication"], "signals": ["resonate", "align", "match", "harmony", "frequency", "sync", "connect"]},
    "threshold": {"description": "Gradual changes reach a critical point causing sudden transformation", "domains": ["physics:phase_transitions", "psychology:learning", "business:tipping_point", "social:revolutions"], "signals": ["threshold", "tipping", "critical", "transform", "sudden", "shift"]},
    "scaling": {"description": "Same structure repeats at different scales", "domains": ["mathematics:fractals", "biology:scaling_laws", "economics:power_laws", "physics:self_similarity"], "signals": ["scale", "fractal", "proportion", "similar", "pattern"]},
    "optimization": {"description": "Systems naturally move toward most efficient configuration", "domains": ["evolution:natural_selection", "physics:least_action", "economics:markets", "mathematics:gradient_descent"], "signals": ["optimize", "efficient", "best", "improve", "evolve", "adapt", "select"]}
}

KNOWLEDGE_BOUNDARY_SIGNALS = {
    "overconfidence": ["definitely", "certainly", "always", "never", "impossible", "guaranteed"],
    "assumption_markers": ["obviously", "of course", "everyone knows", "its clear", "naturally"],
    "coverage_gaps": ["etc", "and so on", "among others", "similar things", "and more"],
    "complexity_avoidance": ["simple", "easy", "just", "merely", "straightforward", "trivial"],
    "recency_bias": ["recent", "current", "latest", "modern", "today", "now"]
}

DOMAIN_BLIND_SPOTS = {
    "technology": ["human behavior change resistance", "second order effects on employment", "regulatory response timelines", "cultural adoption barriers"],
    "business": ["black swan competitive threats", "regulatory disruption timing", "talent market shifts", "customer behavior discontinuities"],
    "medical": ["long-term treatment interactions", "population outlier responses", "psychosocial treatment factors", "environmental variable interactions"],
    "financial": ["correlation breakdown in crisis", "liquidity evaporation timing", "behavioral panic amplification", "regulatory intervention triggers"],
    "social": ["emergent collective behavior", "value shift generational timing", "technology behavior modification", "demographic composition effects"]
}

SCALE_DEFINITIONS = {
    "quantum": {"range": "subatomic", "unit": "nanometer", "time": "nanosecond"},
    "molecular": {"range": "molecular", "unit": "micrometer", "time": "microsecond"},
    "cellular": {"range": "cellular", "unit": "millimeter", "time": "second"},
    "human": {"range": "human", "unit": "meter", "time": "hour"},
    "organizational": {"range": "organizational", "unit": "kilometer", "time": "month"},
    "national": {"range": "national", "unit": "hundred_km", "time": "year"},
    "civilizational": {"range": "civilizational", "unit": "thousand_km", "time": "decade"},
    "planetary": {"range": "planetary", "unit": "earth_radius", "time": "century"},
    "cosmic": {"range": "cosmic", "unit": "light_year", "time": "millennium"}
}

COGNITIVE_GRAMMARS = {
    "mathematics": {"thinking_style": "Abstract symbolic manipulation with absolute certainty", "strength": "precision and universality", "translation_lens": "What is the formal relationship here?"},
    "biology": {"thinking_style": "Dynamic systems optimizing for survival", "strength": "resilience and efficiency over time", "translation_lens": "How does this survive and adapt?"},
    "music": {"thinking_style": "Temporal emotional journey through structured variation", "strength": "emotional resonance and temporal structure", "translation_lens": "What is the tension rhythm and resolution?"},
    "architecture": {"thinking_style": "Form enabling function within constraints", "strength": "structural integrity and purposeful design", "translation_lens": "What structure enables this function?"},
    "economics": {"thinking_style": "Agents optimizing utility under constraints", "strength": "behavioral prediction and resource allocation", "translation_lens": "What are the incentives and constraints?"},
    "psychology": {"thinking_style": "Internal states driving external behavior", "strength": "understanding human motivation", "translation_lens": "What belief or emotion is driving this?"},
    "physics": {"thinking_style": "Universal laws governing matter and energy", "strength": "fundamental principles and predictive power", "translation_lens": "What force energy or conservation law applies?"},
    "narrative": {"thinking_style": "Meaningful journeys through challenge to transformation", "strength": "meaning-making and human engagement", "translation_lens": "Who is the character what is the conflict?"}
}

CIVILIZATIONAL_PATTERNS = {
    "technology_adoption": {"pattern": "S-curve adoption: slow start, explosive growth, plateau", "timescale": "10-50 years", "historical_examples": ["printing press", "electricity", "internet", "mobile"]},
    "institutional_decay": {"pattern": "Institutions built for one era become obstacles in next", "timescale": "50-200 years", "historical_examples": ["feudal systems", "colonial structures", "legacy regulations"]},
    "knowledge_accumulation": {"pattern": "Knowledge compounds exponentially across generations", "timescale": "100-1000 years", "historical_examples": ["scientific revolution", "industrial knowledge", "digital information"]},
    "resource_transition": {"pattern": "Dominant resources shift every few centuries", "timescale": "100-300 years", "historical_examples": ["agricultural land", "coal", "oil", "data"]},
    "power_decentralization": {"pattern": "Technology eventually decentralizes concentrated power", "timescale": "50-150 years", "historical_examples": ["printing press broke church monopoly", "internet broke media monopoly"]}
}

MEANING_ARCHITECTURES = {
    "trust": {"sub_symbolic": "A relational bridge built on repeated positive uncertainty resolution", "emotional_core": "safety_seeking", "depth_score": 9},
    "love": {"sub_symbolic": "A fundamental force of expansion toward another being", "emotional_core": "connection_seeking", "depth_score": 10},
    "fear": {"sub_symbolic": "A protective contraction response to perceived threat", "emotional_core": "survival_protection", "depth_score": 8},
    "success": {"sub_symbolic": "The alignment between desired state and realized state", "emotional_core": "mastery_seeking", "depth_score": 7},
    "pain": {"sub_symbolic": "A consciousness-forcing signal demanding immediate attention", "emotional_core": "damage_response", "depth_score": 9},
    "freedom": {"sub_symbolic": "The unobstructed expression of intrinsic direction", "emotional_core": "autonomy_seeking", "depth_score": 8},
    "justice": {"sub_symbolic": "The restoration of proper relational balance after disruption", "emotional_core": "fairness_seeking", "depth_score": 9},
    "hope": {"sub_symbolic": "The forward projection of present desire into possible futures", "emotional_core": "future_orientation", "depth_score": 8}
}

EMERGENCE_CATALYSTS = [
    "What if the opposite were true?",
    "How would this look from a completely different domain?",
    "What is the simplest possible version of this?",
    "What happens if we remove the most important constraint?",
    "How would nature solve this problem?",
    "What would this look like at 1000x scale?",
    "What does this have in common with music?",
    "What pattern here repeats at every scale?"
]

KNOWN_PARADOXES = {
    "liar": {"operational_resolution": "Treat as meta-statement about language limits - operate at object level"},
    "sorites": {"operational_resolution": "Apply contextual threshold - exact boundary undefined but operational range is clear"},
    "ship_of_theseus": {"operational_resolution": "Define identity by functional continuity not material continuity"},
    "trolley_problem": {"operational_resolution": "Hold both ethical truths - apply contextual weighting based on reversibility and magnitude"},
    "free_will": {"operational_resolution": "Apply determinism for prediction - apply free will for agency"}
}

EXISTING_FIRST_PRINCIPLES = {
    "physics": ["Energy cannot be created or destroyed only transformed", "Objects in motion stay in motion unless acted upon", "Information cannot be destroyed", "Entropy in closed systems always increases"],
    "mathematics": ["A statement is either true or false", "Things equal to the same thing are equal to each other", "Every consistent formal system contains unprovable truths"],
    "biology": ["All living things are made of cells", "Organisms with beneficial traits reproduce more successfully", "Genetic information flows from DNA to RNA to protein"],
    "economics": ["People respond to incentives", "Trade creates value through comparative advantage", "There is no free lunch - all choices have costs"],
    "cognition": ["Attention is a limited resource", "Prediction error drives learning", "Memory is reconstructive not reproductive"]
}

KNOWLEDGE_GAPS = [
    {"domain": "consciousness", "gap": "Why physical processes give rise to subjective experience", "known_edge": "Neural correlates identified but mechanism unknown", "candidate_principle": "Experience may be a fundamental property of information processing at sufficient complexity"},
    {"domain": "intelligence", "gap": "What makes understanding different from pattern matching", "known_edge": "Pattern matching can mimic understanding", "candidate_principle": "Understanding may require grounding in causally active world models"},
    {"domain": "emergence", "gap": "Why simple rules produce unpredictably complex outcomes", "known_edge": "Emergence is documented but not derivable from components", "candidate_principle": "Emergence may be information compression at scale boundaries"},
    {"domain": "time", "gap": "Why time moves in one direction despite symmetric physics", "known_edge": "Thermodynamic arrow identified but philosophical basis unclear", "candidate_principle": "Time asymmetry may be a consequence of information creation not entropy increase"},
    {"domain": "meaning", "gap": "How physical symbol systems acquire genuine meaning", "known_edge": "Symbols manipulated by computers but meaning unclear", "candidate_principle": "Meaning may require causal coupling between symbols and the world they represent"}
]

SEMANTIC_WEIGHTS = {
    "death": 10, "life": 10, "love": 9, "pain": 9, "fear": 9, "hope": 8, "truth": 8, "justice": 8,
    "freedom": 8, "trust": 8, "betrayal": 9, "loss": 8, "joy": 7, "anger": 7, "meaning": 9,
    "purpose": 8, "identity": 8, "connection": 7, "loneliness": 8, "creation": 7, "destruction": 8,
    "war": 9, "peace": 8, "power": 7, "knowledge": 7, "beauty": 6, "home": 6, "family": 7
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
    "just tell me": "underlying cognitive overload needing simplification"
}


def duality_superpose(question, possible_answers, context, api_key):
    log_layer("duality", "superpose", api_key)
    if not question or not possible_answers:
        return {"status": "error", "message": "question and possible_answers required", "layer": "DUALITY"}
    if not isinstance(possible_answers, list) or len(possible_answers) == 0:
        return {"status": "error", "message": "possible_answers must be non-empty list", "layer": "DUALITY"}
    usage_log(api_key, "duality", "superpose")
    question_clean = sanitize_text(question)
    context_clean = sanitize_text(context) if context else ""
    n = len(possible_answers[:10])
    base_prob = 1.0 / n
    states = []
    for answer in possible_answers[:10]:
        answer_text = str(answer)
        answer_words = set(answer_text.lower().split())
        context_words = set((context_clean + " " + question_clean).lower().split())
        overlap = len(answer_words & context_words) / max(len(answer_words), 1)
        context_weight = min(1.0, overlap * 2)
        adjusted_prob = base_prob * (1 + context_weight)
        amplitude = math.sqrt(adjusted_prob)
        states.append({"answer": answer_text[:200], "probability": round(adjusted_prob, 3), "amplitude": round(amplitude, 3), "context_weight": round(context_weight, 3)})
    total_prob = sum(s["probability"] for s in states)
    for s in states:
        s["probability"] = round(s["probability"] / total_prob, 3)
    combined_len = len(question_clean) + len(context_clean)
    context_signal = min(1.0, combined_len / 500)
    scored = sorted(states, key=lambda s: s["amplitude"] * context_signal * s["context_weight"], reverse=True)
    best = scored[0]
    return {"status": "collapsed", "question": question_clean, "best_answer": best["answer"], "confidence": min(100, round(best["amplitude"] * context_signal * 100)), "all_states": scored, "total_states_evaluated": len(states), "layer": "DUALITY"}


def duality_evaluate_paradox(statement_a, statement_b, api_key):
    log_layer("duality", "evaluate_paradox", api_key)
    if not statement_a or not statement_b:
        return {"status": "error", "message": "both statements required", "layer": "DUALITY"}
    usage_log(api_key, "duality", "evaluate_paradox")
    a_lower = statement_a.lower()
    b_lower = statement_b.lower()
    shared = set(a_lower.split()) & set(b_lower.split())
    shared = {t for t in shared if len(t) > 3}
    opposition_words = ["not", "never", "no", "false", "wrong", "impossible", "cannot"]
    a_neg = sum(1 for w in opposition_words if w in a_lower)
    b_neg = sum(1 for w in opposition_words if w in b_lower)
    is_paradox = len(shared) > 2 and abs(a_neg - b_neg) >= 1
    resolution = f"These statements appear contradictory but both contain truth in different contexts. DUALITY holds both simultaneously - context determines which is primary." if is_paradox else "These statements are complementary rather than contradictory"
    return {"status": "evaluated", "is_paradox": is_paradox, "shared_concepts": list(shared)[:10], "resolution": resolution, "can_hold_simultaneously": True, "layer": "DUALITY"}


def akasha_recognize_pattern(text, domain, api_key):
    log_layer("akasha", "recognize_pattern", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "AKASHA"}
    valid, err = validate_text(text, field_name="text")
    if not valid:
        return {"status": "error", "message": err, "layer": "AKASHA"}
    usage_log(api_key, "akasha", "recognize_pattern")
    t_lower = sanitize_text(text).lower()
    detected = {}
    for name, data in UNIVERSAL_PATTERNS.items():
        score = sum(1 for s in data["signals"] if s in t_lower)
        if score > 0:
            detected[name] = {"score": score, "description": data["description"], "domains": data["domains"]}
    if not detected:
        return {"status": "success", "patterns_found": 0, "message": "no universal patterns detected", "layer": "AKASHA"}
    dominant_name, dominant_data = max(detected.items(), key=lambda x: x[1]["score"])
    applications = []
    for domain_entry in dominant_data["domains"][:5]:
        if ":" in domain_entry:
            d, ex = domain_entry.split(":", 1)
        else:
            d, ex = domain_entry, domain_entry
        if d.lower() != domain.lower():
            applications.append({"domain": d, "example": ex, "application": f"Apply {dominant_name} principles from {d} to your context"})
    return {"status": "success", "detected_patterns": list(detected.keys()), "dominant_pattern": dominant_name, "pattern_description": dominant_data["description"], "cross_domain_applications": applications[:4], "layer": "AKASHA"}


def zero_analyze_absence(text, context_type, api_key):
    log_layer("zero", "analyze_absence", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "ZERO"}
    expected_elements = {
        "customer_support": ["apologize", "sorry", "resolve", "help", "solution", "follow up", "timeline", "reference number"],
        "sales": ["price", "discount", "value", "benefit", "guarantee", "call to action", "urgency"],
        "medical": ["diagnosis", "symptoms", "treatment", "dosage", "side effects", "consult doctor", "duration"],
        "legal": ["clause", "party", "agreement", "jurisdiction", "liability", "termination", "confidential"],
        "technical_documentation": ["installation", "requirements", "example", "parameter", "return value", "error handling", "version"],
        "business_proposal": ["objective", "timeline", "budget", "deliverable", "team", "risk", "success criteria"]
    }
    expected = expected_elements.get(context_type)
    if not expected:
        return {"status": "error", "message": f"unknown context type. Available: {list(expected_elements.keys())}", "layer": "ZERO"}
    usage_log(api_key, "zero", "analyze_absence")
    t_lower = sanitize_text(text).lower()
    present = [e for e in expected if e in t_lower]
    absent = [e for e in expected if e not in t_lower]
    completeness = round((len(present) / max(len(expected), 1)) * 100)
    recommendations = [f"consider adding '{missing}' to strengthen this {context_type} response" for missing in absent[:3]]
    return {"status": "success", "context_type": context_type, "completeness_score": completeness, "present_elements": present, "absent_elements": absent, "recommendations": recommendations, "critical_absences": [a for a in absent if a in expected[:3]], "layer": "ZERO"}


def zero_detect_gaps(conversation, api_key):
    log_layer("zero", "detect_gaps", api_key)
    if not conversation:
        return {"status": "error", "message": "conversation required", "layer": "ZERO"}
    usage_log(api_key, "zero", "detect_gaps")
    full_text = " ".join([str(msg) for msg in conversation]).lower()
    gaps = []
    if not any(w in full_text[:100] for w in ["hello", "hi", "hey", "good", "welcome"]):
        gaps.append({"gap": "missing_greeting", "insight": "no greeting detected - may feel abrupt to users"})
    if not any(w in full_text[-200:] for w in ["thank", "bye", "regards", "hope", "feel free"]):
        gaps.append({"gap": "missing_closing", "insight": "no closing statement - conversation ends abruptly"})
    problem_words = ["problem", "issue", "error", "not working", "broken", "failed"]
    solution_words = ["solution", "fix", "resolve", "try this", "here is how", "you can"]
    if any(w in full_text for w in problem_words) and not any(w in full_text for w in solution_words):
        gaps.append({"gap": "missing_solution", "insight": "problem mentioned but no solution offered"})
    return {"status": "success", "gaps_found": len(gaps), "gaps": gaps, "conversation_completeness": max(0, 100 - (len(gaps) * 15)), "layer": "ZERO"}


def deep_process_meaning(text, api_key):
    log_layer("deep", "process_meaning", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "DEEP"}
    valid, err = validate_text(text, field_name="text")
    if not valid:
        return {"status": "error", "message": err, "layer": "DEEP"}
    usage_log(api_key, "deep", "process_meaning")
    text_clean = sanitize_text(text)
    t_lower = text_clean.lower()
    detected = {concept: data for concept, data in MEANING_ARCHITECTURES.items() if concept in t_lower}
    if not detected:
        return {"status": "success", "sub_symbolic_analysis": "text operates at surface symbolic level", "meaning_depth": "shallow", "layer": "DEEP"}
    deepest = max(detected.items(), key=lambda x: x[1]["depth_score"])
    concept, data = deepest
    max_depth = data["depth_score"]
    return {
        "status": "success",
        "detected_concepts": list(detected.keys()),
        "sub_symbolic_meanings": {c: {"sub_symbolic": d["sub_symbolic"], "depth_score": d["depth_score"], "emotional_core": d["emotional_core"]} for c, d in detected.items()},
        "deepest_concept": concept,
        "meaning_depth": "profound" if max_depth >= 9 else "deep" if max_depth >= 7 else "moderate",
        "sub_symbolic_response": f"At the sub-symbolic level this text operates in the space of '{data['sub_symbolic']}'. The core drive is {data['emotional_core'].replace('_', ' ')}.",
        "layer": "DEEP"
    }


def apex_cultivate_emergence(problem, api_key, iterations=3):
    log_layer("apex", "cultivate", api_key)
    if not problem:
        return {"status": "error", "message": "problem required", "layer": "APEX"}
    valid, err = validate_text(problem, field_name="problem")
    if not valid:
        return {"status": "error", "message": err, "layer": "APEX"}
    iterations = min(max(iterations, 1), 5)
    usage_log(api_key, "apex", "cultivate")
    problem_clean = sanitize_text(problem)
    emergent_insights = []
    used_catalysts = []
    for i in range(iterations):
        available = [c for c in EMERGENCE_CATALYSTS if c not in used_catalysts]
        if not available:
            break
        catalyst = random.choice(available)
        used_catalysts.append(catalyst)
        words = problem_clean.split()[:10]
        core = " ".join(words)
        domains = ["biology", "music", "architecture", "physics", "cooking"]
        domain = domains[i % len(domains)]
        domain_analogies = {"biology": "how cells adapt to environmental pressure", "music": "how harmony emerges from individual notes", "architecture": "how structure enables function", "physics": "how energy flows along paths of least resistance", "cooking": "how heat transforms raw ingredients into something new"}
        insight = f"Iteration {i+1} - {catalyst} - Applied to '{core[:60]}': consider this through {domain} lens where {domain_analogies.get(domain, 'patterns repeat at every scale')}"
        emergent_insights.append({"iteration": i + 1, "catalyst": catalyst, "emergent_thought": insight})
    synthesis = f"Across {len(emergent_insights)} iterations of emergence cultivation, a pattern emerges: '{problem_clean[:80]}' reveals novel solution paths when viewed through unexpected domains. The unexpected connection: combine the first and last insights for maximum emergence."
    return {"status": "success", "problem": problem_clean[:200], "iterations_run": iterations, "emergent_insights": emergent_insights, "synthesized_emergence": synthesis, "emergence_score": min(100, len(emergent_insights) * 20 + 20), "layer": "APEX"}


def babel_translate_domain(concept, source_domain, target_domain, api_key):
    log_layer("babel", "translate_domain", api_key)
    if not concept or not source_domain or not target_domain:
        return {"status": "error", "message": "concept, source_domain and target_domain required", "layer": "BABEL"}
    valid, err = validate_text(concept, field_name="concept")
    if not valid:
        return {"status": "error", "message": err, "layer": "BABEL"}
    if source_domain not in COGNITIVE_GRAMMARS:
        return {"status": "error", "message": f"unknown source domain. Available: {list(COGNITIVE_GRAMMARS.keys())}", "layer": "BABEL"}
    if target_domain not in COGNITIVE_GRAMMARS:
        return {"status": "error", "message": f"unknown target domain. Available: {list(COGNITIVE_GRAMMARS.keys())}", "layer": "BABEL"}
    usage_log(api_key, "babel", "translate_domain")
    concept_clean = sanitize_text(concept)
    source = COGNITIVE_GRAMMARS[source_domain]
    target = COGNITIVE_GRAMMARS[target_domain]
    translation = f"'{concept_clean[:100]}' in {source['thinking_style'][:60]} translates to {target['thinking_style'][:60]}. Key question: {target['translation_lens']} This brings {target['strength']} to bear on the problem."
    novel_insight = f"The unexpected insight from translating {concept_clean[:50]} from {source_domain} to {target_domain}: patterns that appear fixed in one domain become dynamic and malleable in the other, revealing hidden solution spaces."
    return {"status": "success", "concept": concept_clean[:200], "source_domain": source_domain, "target_domain": target_domain, "translation": translation, "novel_insight": novel_insight, "layer": "BABEL"}


def eternal_analyze_impact(decision, domain, api_key, time_horizon_years=100):
    log_layer("eternal", "analyze_impact", api_key)
    if not decision:
        return {"status": "error", "message": "decision required", "layer": "ETERNAL"}
    valid, err = validate_text(decision, field_name="decision")
    if not valid:
        return {"status": "error", "message": err, "layer": "ETERNAL"}
    time_horizon_years = min(max(time_horizon_years, 10), 1000)
    usage_log(api_key, "eternal", "analyze_impact")
    decision_clean = sanitize_text(decision)
    d_lower = decision_clean.lower()
    matching = []
    for name, data in CIVILIZATIONAL_PATTERNS.items():
        if any(w in d_lower for w in name.split("_")):
            matching.append({"pattern": name, "description": data["pattern"], "timescale": data["timescale"], "historical_parallel": data["historical_examples"][0]})
    generational_impact = {
        10: {"scope": "1_generation", "description": "Affects current workforce and children"},
        30: {"scope": "2_generations", "description": "Affects grandchildren and institutions"},
        100: {"scope": "5_generations", "description": "Affects fundamental social structures"},
        300: {"scope": "10_generations", "description": "Affects language culture and values"},
        1000: {"scope": "civilization", "description": "Affects what kind of civilization humans become"}
    }
    gen_impact = {"scope": "civilization", "description": "Affects what kind of civilization humans become"}
    for threshold, impact in sorted(generational_impact.items()):
        if time_horizon_years <= threshold:
            gen_impact = impact
            break
    trajectory = f"Over {time_horizon_years} years following {matching[0]['pattern']} pattern. Historical parallel: {matching[0]['historical_parallel']}." if matching else f"Over {time_horizon_years} years decisions of this type reshape institutional and cultural landscape significantly."
    recommendation = f"Build reversibility into implementation. Plan for plateau phase after explosive growth." if matching else "Consider generational consequences. Prioritize reversibility over optimization."
    return {"status": "success", "decision": decision_clean[:200], "time_horizon_years": time_horizon_years, "matching_civilizational_patterns": matching[:3], "generational_impact": gen_impact, "civilizational_trajectory": trajectory, "long_term_recommendation": recommendation, "layer": "ETERNAL"}


def infinite_process_paradox(statement, api_key):
    log_layer("infinite", "process_paradox", api_key)
    if not statement:
        return {"status": "error", "message": "statement required", "layer": "INFINITE"}
    valid, err = validate_text(statement, field_name="statement")
    if not valid:
        return {"status": "error", "message": err, "layer": "INFINITE"}
    usage_log(api_key, "infinite", "process_paradox")
    s_lower = sanitize_text(statement).lower()
    paradox_type = "vagueness"
    if any(w in s_lower for w in ["this statement", "i am lying", "self-refer"]):
        paradox_type = "self_referential"
    elif any(w in s_lower for w in ["kill", "harm", "sacrifice", "ethical", "moral"]):
        paradox_type = "ethical_dilemma"
    elif any(w in s_lower for w in ["same", "identity", "change", "replace"]):
        paradox_type = "identity"
    elif any(w in s_lower for w in ["free will", "determined", "choice", "fate"]):
        paradox_type = "philosophical"
    resolutions = {
        "self_referential": "Treat as meta-level statement about language limits - operate at object level",
        "ethical_dilemma": "Both ethical claims are valid - apply contextual priority based on reversibility and magnitude",
        "identity": "Identity is continuous not binary - define by functional purpose not material composition",
        "philosophical": "Both frameworks describe different levels of reality - use each where appropriate",
        "vagueness": "Apply contextual threshold - exact boundary undefined but operational range is clear"
    }
    for name, data in KNOWN_PARADOXES.items():
        if name.replace("_", " ") in s_lower:
            return {"status": "processed", "statement": statement[:200], "paradox_type": paradox_type, "known_paradox": name, "operational_resolution": data["operational_resolution"], "can_operate_without_resolution": True, "layer": "INFINITE"}
    return {"status": "processed", "statement": statement[:200], "paradox_type": paradox_type, "operational_resolution": resolutions.get(paradox_type, "Hold contradiction without forcing resolution - operate contextually"), "can_operate_without_resolution": True, "layer": "INFINITE"}


def infinite_hold_contradiction(position_a, position_b, context, api_key):
    log_layer("infinite", "hold_contradiction", api_key)
    if not position_a or not position_b:
        return {"status": "error", "message": "both positions required", "layer": "INFINITE"}
    usage_log(api_key, "infinite", "hold_contradiction")
    a_clean = sanitize_text(position_a)
    b_clean = sanitize_text(position_b)
    context_clean = sanitize_text(context) if context else ""
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
    synthesis = f"INFINITE synthesis: Both '{a_clean[:60]}' and '{b_clean[:60]}' contain truth. They describe different aspects of the same reality. Operational priority determined by: reversibility, magnitude, and stakeholder impact."
    return {"status": "held", "truth_score_a": round(truth_a, 2), "truth_score_b": round(truth_b, 2), "contextual_priority": priority, "synthesis": synthesis, "both_valid": True, "layer": "INFINITE"}


def abyss_detect_blind_spots(text, domain, api_key):
    log_layer("abyss", "detect_blind_spots", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "ABYSS"}
    valid, err = validate_text(text, field_name="text")
    if not valid:
        return {"status": "error", "message": err, "layer": "ABYSS"}
    usage_log(api_key, "abyss", "detect_blind_spots")
    t_lower = sanitize_text(text).lower()
    boundary_signals = {}
    for signal_type, patterns in KNOWLEDGE_BOUNDARY_SIGNALS.items():
        found = [p for p in patterns if p in t_lower]
        if found:
            boundary_signals[signal_type] = found
    domain_spots = DOMAIN_BLIND_SPOTS.get(domain, [])
    uu_signatures = []
    certainty_words = ["definitely", "certainly", "always", "guaranteed", "obviously"]
    solution_words = ["solution", "fix", "answer", "resolve"]
    risk_words = ["risk", "challenge", "problem", "issue", "concern", "failure"]
    if any(w in t_lower for w in certainty_words) and len(t_lower.split()) > 50:
        uu_signatures.append({"signature": "High confidence in complex domain", "risk": "Unknown factors masking as known ones"})
    if any(w in t_lower for w in solution_words) and not any(w in t_lower for w in risk_words):
        uu_signatures.append({"signature": "Solution without risks mentioned", "risk": "Blindness to how plans fail"})
    blind_spot_score = min(100, len(boundary_signals) * 10 + len(uu_signatures) * 15)
    warnings = []
    if "overconfidence" in boundary_signals:
        warnings.append("Overconfidence signals detected - may be masking unknown factors")
    if "assumption_markers" in boundary_signals:
        warnings.append("Assumed knowledge detected - challenge these assumptions explicitly")
    recommendations = ["Map the explicit boundaries of what you know"] + [f"Explicitly investigate: {spot}" for spot in domain_spots[:2]]
    return {"status": "analyzed", "domain": domain, "boundary_signals_detected": boundary_signals, "unknown_unknown_signatures": uu_signatures, "domain_known_blind_spots": domain_spots[:4], "blind_spot_risk_score": blind_spot_score, "awareness_score": max(0, 100 - blind_spot_score), "warnings": warnings, "recommendations": recommendations, "layer": "ABYSS"}


def fractal_analyze_at_scale(problem, scale, api_key):
    log_layer("fractal", "analyze_at_scale", api_key)
    if not problem or not scale:
        return {"status": "error", "message": "problem and scale required", "layer": "FRACTAL"}
    valid, err = validate_text(problem, field_name="problem")
    if not valid:
        return {"status": "error", "message": err, "layer": "FRACTAL"}
    if scale not in SCALE_DEFINITIONS:
        return {"status": "error", "message": f"unknown scale. Available: {list(SCALE_DEFINITIONS.keys())}", "layer": "FRACTAL"}
    usage_log(api_key, "fractal", "analyze_at_scale")
    problem_clean = sanitize_text(problem)
    scale_data = SCALE_DEFINITIONS[scale]
    analyses = {
        "quantum": f"At quantum scale: '{problem_clean[:60]}' involves fundamental uncertainty and superposition of states",
        "molecular": f"At molecular scale: '{problem_clean[:60]}' involves bonding energy states and chemical transformation",
        "cellular": f"At cellular scale: '{problem_clean[:60]}' involves signaling metabolism and adaptive response",
        "human": f"At human scale: '{problem_clean[:60]}' involves cognition behavior and interpersonal dynamics",
        "organizational": f"At organizational scale: '{problem_clean[:60]}' involves coordination culture and resource allocation",
        "national": f"At national scale: '{problem_clean[:60]}' involves policy institutions and collective behavior",
        "civilizational": f"At civilizational scale: '{problem_clean[:60]}' involves long-term trajectory and fundamental values",
        "planetary": f"At planetary scale: '{problem_clean[:60]}' involves ecosystem dynamics and species-level patterns",
        "cosmic": f"At cosmic scale: '{problem_clean[:60]}' involves fundamental laws of information and energy"
    }
    return {"status": "success", "problem": problem_clean[:200], "scale": scale, "scale_range": scale_data["range"], "characteristic_unit": scale_data["unit"], "characteristic_time": scale_data["time"], "scale_specific_analysis": analyses.get(scale, f"At {scale} scale: analyzing '{problem_clean[:60]}'"), "scale_insight": f"Viewing '{problem_clean[:60]}' at {scale} scale reveals dynamics operating at {scale_data['time']} timescales.", "layer": "FRACTAL"}


def origin_generate_first_principle(domain, api_key):
    log_layer("origin", "generate", api_key)
    if not domain:
        return {"status": "error", "message": "domain required", "layer": "ORIGIN"}
    valid, err = validate_text(domain, max_length=200, field_name="domain")
    if not valid:
        return {"status": "error", "message": err, "layer": "ORIGIN"}
    usage_log(api_key, "origin", "generate")
    domain_clean = sanitize_text(domain)
    d_lower = domain_clean.lower()
    existing = []
    for known_domain, principles in EXISTING_FIRST_PRINCIPLES.items():
        if known_domain in d_lower or d_lower in known_domain:
            existing = principles[:3]
            break
    if not existing:
        existing = EXISTING_FIRST_PRINCIPLES["cognition"]
    gaps = [g for g in KNOWLEDGE_GAPS if g["domain"] in d_lower or d_lower in g["domain"]]
    generated = [
        {"method": "inversion", "candidate": f"Inverse principle: What if the opposite of '{existing[0][:50]}' is true in specific conditions?"},
        {"method": "generalization", "candidate": f"Unifying principle for {domain_clean}: all specific instances may be manifestations of a single conservation law"},
        {"method": "boundary_probe", "candidate": f"At the boundary of {domain_clean}: principles governing extreme conditions may differ fundamentally from normal conditions"},
        {"method": "unity_search", "candidate": f"Multiple observed regularities in {domain_clean} may be different aspects of a single deeper invariant"}
    ]
    novel = gaps[0]["candidate_principle"] if gaps else f"Candidate principle for {domain_clean}: The most fundamental regularity may be an information-theoretic constraint rather than a physical one."
    return {"status": "generated", "domain": domain_clean, "existing_principles": existing, "known_knowledge_gaps": gaps[:2], "generated_candidates": generated, "most_novel_candidate": novel, "confidence": "speculative", "note": "These are candidate principles requiring rigorous testing", "layer": "ORIGIN"}
