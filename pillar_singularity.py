import math
import random


UNIVERSAL_PATTERNS = {
    "branching": {"description": "A central source divides into multiple paths", "domains": ["biology:trees", "geology:rivers", "neuroscience:neurons", "business:org_charts"], "signals": ["branch", "divide", "split", "fork", "tree", "network", "spread"]},
    "cycles": {"description": "Recurring patterns that return to their origin", "domains": ["astronomy:orbits", "biology:seasons", "economics:business_cycles"], "signals": ["cycle", "repeat", "return", "loop", "periodic", "recurring", "rotate"]},
    "emergence": {"description": "Simple components create complex unexpected behavior", "domains": ["biology:consciousness", "economics:markets", "physics:thermodynamics"], "signals": ["emerge", "arise", "appear", "complex", "unexpected", "collective", "system"]},
    "compression": {"description": "Large complex things reduce to essential core", "domains": ["physics:black_holes", "mathematics:compression", "biology:DNA"], "signals": ["compress", "reduce", "simplify", "distill", "core", "essential", "summary"]},
    "resonance": {"description": "Matching frequencies amplify each other", "domains": ["physics:sound", "psychology:rapport", "economics:markets"], "signals": ["resonate", "align", "match", "harmony", "frequency", "sync", "connect"]},
    "threshold": {"description": "Gradual changes reach a critical point causing sudden transformation", "domains": ["physics:phase_transitions", "psychology:learning", "business:tipping_point"], "signals": ["threshold", "tipping", "critical", "transform", "sudden", "shift"]},
    "scaling": {"description": "Same structure repeats at different scales", "domains": ["mathematics:fractals", "biology:scaling_laws", "economics:power_laws"], "signals": ["scale", "fractal", "proportion", "similar", "pattern"]},
    "optimization": {"description": "Systems naturally move toward most efficient configuration", "domains": ["evolution:natural_selection", "physics:least_action", "economics:markets"], "signals": ["optimize", "efficient", "best", "improve", "evolve", "adapt", "select"]}
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

EXISTING_FIRST_PRINCIPLES = {
    "physics": ["Energy cannot be created or destroyed only transformed", "Objects in motion stay in motion unless acted upon", "Information cannot be destroyed", "Entropy in closed systems always increases"],
    "mathematics": ["A statement is either true or false", "Things equal to the same thing are equal to each other", "Every consistent formal system contains unprovable truths"],
    "biology": ["All living things are made of cells", "Organisms with beneficial traits reproduce more successfully", "Genetic information flows from DNA to RNA to protein"],
    "economics": ["People respond to incentives", "Trade creates value through comparative advantage", "There is no free lunch - all choices have costs"],
    "cognition": ["Attention is a limited resource", "Prediction error drives learning", "Memory is reconstructive not reproductive"],
    "ai": ["Intelligence requires representation and search", "Learning requires signal and feedback", "Generalization requires abstraction beyond training data"]
}

KNOWLEDGE_GAPS = [
    {"domain": "consciousness", "gap": "Why physical processes give rise to subjective experience", "known_edge": "Neural correlates identified but mechanism unknown", "candidate_principle": "Experience may be a fundamental property of information processing at sufficient complexity"},
    {"domain": "intelligence", "gap": "What makes understanding different from pattern matching", "known_edge": "Pattern matching can mimic understanding but cannot ground meaning", "candidate_principle": "Understanding requires grounding in causally active world models"},
    {"domain": "emergence", "gap": "Why simple rules produce unpredictably complex outcomes", "known_edge": "Emergence is documented but not derivable from components", "candidate_principle": "Emergence may be information compression at scale boundaries"},
    {"domain": "meaning", "gap": "How physical symbol systems acquire genuine meaning", "known_edge": "Symbols manipulated by computers but meaning origin unclear", "candidate_principle": "Meaning requires causal coupling between symbols and the world they represent"}
]

EXPECTED_ELEMENTS = {
    "customer_support": ["apologize", "sorry", "resolve", "help", "solution", "follow up", "timeline"],
    "sales": ["price", "discount", "value", "benefit", "guarantee", "call to action", "urgency"],
    "medical": ["diagnosis", "symptoms", "treatment", "dosage", "side effects", "consult doctor"],
    "legal": ["clause", "party", "agreement", "jurisdiction", "liability", "termination"],
    "technical_documentation": ["installation", "requirements", "example", "parameter", "return value", "error handling"],
    "business_proposal": ["objective", "timeline", "budget", "deliverable", "team", "risk", "success criteria"]
}


def duality_superpose(question, possible_answers, context, api_key, db):
    try:
        if not question or not possible_answers:
            return {"status": "error", "message": "question and possible_answers required", "layer": "DUALITY"}
        if not isinstance(possible_answers, list) or len(possible_answers) == 0:
            return {"status": "error", "message": "possible_answers must be non-empty list", "layer": "DUALITY"}
        if len(possible_answers) > 20:
            return {"status": "error", "message": "max 20 possible answers", "layer": "DUALITY"}
        question_clean = question.replace('\x00', '').strip()
        context_clean = (context or "").replace('\x00', '').strip()
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "DUALITY", "action": "superpose"}).execute()
        return {"status": "collapsed", "question": question_clean, "best_answer": best["answer"], "confidence": min(100, round(best["amplitude"] * context_signal * 100)), "all_states": scored, "total_states_evaluated": len(states), "layer": "DUALITY", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "superposition failed", "layer": "DUALITY"}


def duality_evaluate_paradox(statement_a, statement_b, api_key, db):
    try:
        if not statement_a or not statement_b:
            return {"status": "error", "message": "both statements required", "layer": "DUALITY"}
        a_lower = statement_a.lower()
        b_lower = statement_b.lower()
        shared = set(a_lower.split()) & set(b_lower.split())
        shared = {t for t in shared if len(t) > 3}
        opposition_words = ["not", "never", "no", "false", "wrong", "impossible", "cannot"]
        a_neg = sum(1 for w in opposition_words if w in a_lower)
        b_neg = sum(1 for w in opposition_words if w in b_lower)
        is_paradox = len(shared) > 2 and abs(a_neg - b_neg) >= 1
        resolution = "These statements appear contradictory but both contain truth in different contexts. DUALITY holds both simultaneously - context determines which is primary." if is_paradox else "These statements are complementary rather than contradictory."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "DUALITY", "action": "evaluate_paradox"}).execute()
        return {"status": "evaluated", "is_paradox": is_paradox, "shared_concepts": list(shared)[:10], "resolution": resolution, "can_hold_simultaneously": True, "layer": "DUALITY", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "paradox evaluation failed", "layer": "DUALITY"}


def akasha_recognize_pattern(text, domain, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "AKASHA"}
        if len(text) > 10000:
            return {"status": "error", "message": "text too long", "layer": "AKASHA"}
        t_lower = text.replace('\x00', '').strip().lower()
        detected = {}
        for name, data in UNIVERSAL_PATTERNS.items():
            score = sum(1 for s in data["signals"] if s in t_lower)
            if score > 0:
                detected[name] = {"score": score, "description": data["description"], "domains": data["domains"]}
        if not detected:
            return {"status": "success", "patterns_found": 0, "message": "no universal patterns detected", "layer": "AKASHA", "pillar": "SINGULARITY_ENGINE"}
        dominant_name, dominant_data = max(detected.items(), key=lambda x: x[1]["score"])
        applications = []
        for domain_entry in dominant_data["domains"][:5]:
            if ":" in domain_entry:
                d, ex = domain_entry.split(":", 1)
            else:
                d, ex = domain_entry, domain_entry
            if d.lower() != domain.lower():
                applications.append({"domain": d, "example": ex, "application": f"Apply {dominant_name} principles from {d} to your context"})
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "AKASHA", "action": "recognize_pattern"}).execute()
        return {"status": "success", "detected_patterns": list(detected.keys()), "dominant_pattern": dominant_name, "pattern_description": dominant_data["description"], "cross_domain_applications": applications[:4], "layer": "AKASHA", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "pattern recognition failed", "layer": "AKASHA"}


def akasha_cross_domain_transfer(pattern, source_domain, target_domain, api_key, db):
    try:
        if not pattern or not source_domain or not target_domain:
            return {"status": "error", "message": "pattern, source_domain and target_domain required", "layer": "AKASHA"}
        universal_pattern = None
        for name, data in UNIVERSAL_PATTERNS.items():
            if pattern.lower() in name or name in pattern.lower():
                universal_pattern = data
                break
        if universal_pattern:
            transfer = f"The {pattern} pattern from {source_domain} manifests in {target_domain} as: {universal_pattern['description']}. This cross-domain transfer reveals: apply the same structural logic that makes it work in {source_domain} to solve problems in {target_domain}."
        else:
            transfer = f"Transfer the structural logic of '{pattern}' from {source_domain} to {target_domain}. Look for analogous structures, similar constraints, and parallel optimization pressures."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "AKASHA", "action": "cross_domain_transfer"}).execute()
        return {"status": "success", "pattern": pattern, "source_domain": source_domain, "target_domain": target_domain, "transfer_insight": transfer, "layer": "AKASHA", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "cross domain transfer failed", "layer": "AKASHA"}


def zero_analyze_absence(text, context_type, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "ZERO"}
        if context_type not in EXPECTED_ELEMENTS:
            return {"status": "error", "message": f"unknown context type. Available: {list(EXPECTED_ELEMENTS.keys())}", "layer": "ZERO"}
        if len(text) > 10000:
            return {"status": "error", "message": "text too long", "layer": "ZERO"}
        expected = EXPECTED_ELEMENTS[context_type]
        t_lower = text.replace('\x00', '').strip().lower()
        present = [e for e in expected if e in t_lower]
        absent = [e for e in expected if e not in t_lower]
        completeness = round((len(present) / max(len(expected), 1)) * 100)
        recommendations = [f"Consider adding '{missing}' to strengthen this {context_type} response" for missing in absent[:3]]
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ZERO", "action": "analyze_absence"}).execute()
        return {"status": "success", "context_type": context_type, "completeness_score": completeness, "present_elements": present, "absent_elements": absent, "recommendations": recommendations, "critical_absences": absent[:3], "layer": "ZERO", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "absence analysis failed", "layer": "ZERO"}


def zero_detect_gaps(conversation, api_key, db):
    try:
        if not conversation or not isinstance(conversation, list):
            return {"status": "error", "message": "conversation list required", "layer": "ZERO"}
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
        question_words = ["what", "how", "why", "when", "where"]
        answer_words = ["because", "the reason", "here is", "you can", "the answer", "specifically"]
        if any(w in full_text for w in question_words) and not any(w in full_text for w in answer_words):
            gaps.append({"gap": "missing_answer", "insight": "questions asked but answers may be missing"})
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ZERO", "action": "detect_gaps"}).execute()
        return {"status": "success", "gaps_found": len(gaps), "gaps": gaps, "conversation_completeness": max(0, 100 - (len(gaps) * 15)), "layer": "ZERO", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "gap detection failed", "layer": "ZERO"}


def zero_find_data_gaps(dataset, expected_fields, api_key, db):
    try:
        if not isinstance(dataset, list) or not isinstance(expected_fields, list):
            return {"status": "error", "message": "dataset and expected_fields must be lists", "layer": "ZERO"}
        if len(dataset) > 1000:
            return {"status": "error", "message": "max 1000 rows per analysis", "layer": "ZERO"}
        missing_by_field = {}
        for field in expected_fields:
            missing_count = sum(1 for row in dataset if not row.get(field))
            if missing_count > 0:
                missing_by_field[field] = {"missing_count": missing_count, "missing_percent": round((missing_count / len(dataset)) * 100, 1)}
        completeness = round((1 - len(missing_by_field) / max(len(expected_fields), 1)) * 100)
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ZERO", "action": "find_data_gaps"}).execute()
        return {"status": "success", "rows_analyzed": len(dataset), "expected_fields": expected_fields, "missing_fields": missing_by_field, "completeness_score": completeness, "recommendation": "Address missing fields before analysis" if missing_by_field else "Dataset appears complete", "layer": "ZERO", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "data gap analysis failed", "layer": "ZERO"}


def apex_cultivate_emergence(problem, api_key, db, iterations=3):
    try:
        if not problem:
            return {"status": "error", "message": "problem required", "layer": "APEX"}
        if len(problem) > 10000:
            return {"status": "error", "message": "problem too long", "layer": "APEX"}
        iterations = min(max(iterations, 1), 5)
        problem_clean = problem.replace('\x00', '').strip()
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
            insight = f"Iteration {i+1}: {catalyst} Applied to '{core[:60]}' through {domain} lens - {domain_analogies.get(domain, 'patterns repeat at every scale')}. This reveals an emergent property not visible from the original framing."
            emergent_insights.append({"iteration": i + 1, "catalyst": catalyst, "domain_lens": domain, "emergent_thought": insight})
        synthesis = f"Across {len(emergent_insights)} iterations of emergence cultivation for '{problem_clean[:60]}', a meta-pattern emerges: the solution exists in the space between existing frameworks. The unexpected connection: combine the first and last insights for maximum emergence."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "APEX", "action": "cultivate_emergence"}).execute()
        return {"status": "success", "problem": problem_clean[:200], "iterations_run": iterations, "emergent_insights": emergent_insights, "synthesized_emergence": synthesis, "emergence_score": min(100, len(emergent_insights) * 20 + 20), "layer": "APEX", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "emergence cultivation failed", "layer": "APEX"}


def apex_amplify_thinking(thought, api_key, db):
    try:
        if not thought:
            return {"status": "error", "message": "thought required", "layer": "APEX"}
        if len(thought) > 10000:
            return {"status": "error", "message": "thought too long", "layer": "APEX"}
        thought_clean = thought.replace('\x00', '').strip()
        amplifications = []
        amplifications.append(f"Scale up: What happens when '{thought_clean[:80]}' is applied at planetary scale?")
        amplifications.append(f"Scale down: What happens when '{thought_clean[:80]}' is applied at quantum scale?")
        amplifications.append(f"Inversion: What if the opposite of '{thought_clean[:80]}' is actually more useful?")
        amplifications.append(f"Time extension: How does '{thought_clean[:80]}' look in 1000 years?")
        amplifications.append(f"Cross-domain: How would biology solve '{thought_clean[:80]}'?")
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "APEX", "action": "amplify_thinking"}).execute()
        return {"status": "success", "original_thought": thought_clean[:200], "amplified_thoughts": amplifications, "amplification_count": len(amplifications), "layer": "APEX", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "thought amplification failed", "layer": "APEX"}


def fractal_analyze_at_scale(problem, scale, api_key, db):
    try:
        if not problem or not scale:
            return {"status": "error", "message": "problem and scale required", "layer": "FRACTAL"}
        if scale not in SCALE_DEFINITIONS:
            return {"status": "error", "message": f"unknown scale. Available: {list(SCALE_DEFINITIONS.keys())}", "layer": "FRACTAL"}
        if len(problem) > 10000:
            return {"status": "error", "message": "problem too long", "layer": "FRACTAL"}
        problem_clean = problem.replace('\x00', '').strip()
        scale_data = SCALE_DEFINITIONS[scale]
        analyses = {
            "quantum": f"At quantum scale: '{problem_clean[:60]}' involves fundamental uncertainty and superposition of states. Every possible outcome exists simultaneously until observation collapses to one reality.",
            "molecular": f"At molecular scale: '{problem_clean[:60]}' involves bonding energy states and chemical transformation. Structure determines function at this level.",
            "cellular": f"At cellular scale: '{problem_clean[:60]}' involves signaling metabolism and adaptive response. Cells are the fundamental unit of life-level intelligence.",
            "human": f"At human scale: '{problem_clean[:60]}' involves cognition behavior and interpersonal dynamics. This is the scale where meaning lives.",
            "organizational": f"At organizational scale: '{problem_clean[:60]}' involves coordination culture and resource allocation. The challenge is alignment of individual and collective interest.",
            "national": f"At national scale: '{problem_clean[:60]}' involves policy institutions and collective behavior. Governance and incentive structures dominate.",
            "civilizational": f"At civilizational scale: '{problem_clean[:60]}' involves long-term trajectory and fundamental values. What kind of civilization does this create?",
            "planetary": f"At planetary scale: '{problem_clean[:60]}' involves ecosystem dynamics and species-level patterns. Sustainability becomes the primary constraint.",
            "cosmic": f"At cosmic scale: '{problem_clean[:60]}' involves fundamental laws of information and energy. Only conservation laws and information theory apply at this level."
        }
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "FRACTAL", "action": "analyze_at_scale"}).execute()
        return {"status": "success", "problem": problem_clean[:200], "scale": scale, "scale_range": scale_data["range"], "characteristic_unit": scale_data["unit"], "characteristic_time": scale_data["time"], "scale_specific_analysis": analyses.get(scale, f"At {scale} scale: {problem_clean[:60]}"), "scale_insight": f"Viewing '{problem_clean[:60]}' at {scale} scale reveals dynamics operating at {scale_data['time']} timescales.", "layer": "FRACTAL", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "fractal analysis failed", "layer": "FRACTAL"}


def fractal_multi_scale_analysis(problem, scales, api_key, db):
    try:
        if not problem or not scales:
            return {"status": "error", "message": "problem and scales required", "layer": "FRACTAL"}
        if not isinstance(scales, list) or len(scales) == 0:
            return {"status": "error", "message": "scales must be non-empty list", "layer": "FRACTAL"}
        if len(scales) > 9:
            return {"status": "error", "message": "max 9 scales per analysis", "layer": "FRACTAL"}
        results = []
        for scale in scales:
            if scale in SCALE_DEFINITIONS:
                result = fractal_analyze_at_scale(problem, scale, api_key, db)
                results.append(result)
        self_similar = "The problem shows self-similar patterns across multiple scales - the same core dynamic appears differently at each level." if len(results) > 2 else "Analyze across more scales to detect self-similarity."
        return {"status": "success", "problem": problem[:200], "scales_analyzed": len(results), "results": results, "self_similarity_observation": self_similar, "layer": "FRACTAL", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "multi-scale analysis failed", "layer": "FRACTAL"}


def origin_generate_first_principle(domain, api_key, db):
    try:
        if not domain:
            return {"status": "error", "message": "domain required", "layer": "ORIGIN"}
        if len(domain) > 200:
            return {"status": "error", "message": "domain too long", "layer": "ORIGIN"}
        domain_clean = domain.replace('\x00', '').strip()
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
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ORIGIN", "action": "generate_first_principle"}).execute()
        return {"status": "generated", "domain": domain_clean, "existing_principles": existing, "known_knowledge_gaps": gaps[:2], "generated_candidates": generated, "most_novel_candidate": novel, "confidence": "speculative", "note": "These are candidate principles requiring rigorous testing", "layer": "ORIGIN", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "first principle generation failed", "layer": "ORIGIN"}


def origin_probe_knowledge_gap(domain, question, api_key, db):
    try:
        if not domain or not question:
            return {"status": "error", "message": "domain and question required", "layer": "ORIGIN"}
        domain_clean = domain.replace('\x00', '').strip()
        question_clean = question.replace('\x00', '').strip()
        d_lower = domain_clean.lower()
        gaps = [g for g in KNOWLEDGE_GAPS if g["domain"] in d_lower or d_lower in g["domain"]]
        q_lower = question_clean.lower()
        known_words = set()
        for gap in gaps:
            known_words.update(gap["known_edge"].lower().split())
        question_words = set(q_lower.split())
        uncovered = question_words - known_words
        uncovered = {w for w in uncovered if len(w) > 4}
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ORIGIN", "action": "probe_knowledge_gap"}).execute()
        return {"status": "probed", "domain": domain_clean, "question": question_clean[:200], "known_gaps_in_domain": [g["gap"] for g in gaps], "question_edges_beyond_knowledge": list(uncovered)[:5], "frontier_note": f"The question '{question_clean[:80]}' probes beyond the current knowledge frontier in {domain_clean}" if uncovered else f"This question appears within current knowledge bounds for {domain_clean}", "layer": "ORIGIN", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "knowledge gap probe failed", "layer": "ORIGIN"}


def origin_map_frontier(domains, api_key, db):
    try:
        if not isinstance(domains, list) or len(domains) == 0:
            return {"status": "error", "message": "domains list required", "layer": "ORIGIN"}
        if len(domains) > 10:
            return {"status": "error", "message": "max 10 domains per frontier map", "layer": "ORIGIN"}
        frontier_map = {}
        for domain in domains:
            d_lower = domain.lower()
            gaps = [g for g in KNOWLEDGE_GAPS if g["domain"] in d_lower or d_lower in g["domain"]]
            existing = []
            for known_domain, principles in EXISTING_FIRST_PRINCIPLES.items():
                if known_domain in d_lower or d_lower in known_domain:
                    existing = principles
                    break
            frontier_map[domain] = {"known_principles": len(existing), "known_gaps": len(gaps), "frontier_description": gaps[0]["gap"] if gaps else "No mapped gaps - may be well-understood or unexplored territory", "candidate_principle": gaps[0]["candidate_principle"] if gaps else f"Investigate {domain} for unmapped principles at knowledge boundaries"}
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ORIGIN", "action": "map_frontier"}).execute()
        return {"status": "mapped", "domains": domains, "frontier_map": frontier_map, "total_domains": len(frontier_map), "layer": "ORIGIN", "pillar": "SINGULARITY_ENGINE"}
    except Exception as e:
        return {"status": "error", "message": "frontier mapping failed", "layer": "ORIGIN"}
