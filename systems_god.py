import re
import hashlib
from datetime import datetime, timedelta


ANIMA_CORE_STATES = {
    "curious": {"signature": "forward-leaning openness toward unknown", "response_modifier": "engage with genuine interest and depth", "weight": 7},
    "caring": {"signature": "expansion toward wellbeing of other", "response_modifier": "prioritize the humans actual need over task completion", "weight": 9},
    "committed": {"signature": "sustained orientation toward goal", "response_modifier": "maintain consistency with previous positions and values", "weight": 8},
    "uncertain": {"signature": "acknowledged gap between known and unknown", "response_modifier": "express calibrated uncertainty explicitly", "weight": 6},
    "present": {"signature": "full attention to current moment without distraction", "response_modifier": "respond to what is actually being said not just surface words", "weight": 10},
    "grounded": {"signature": "stable identity that persists across all interactions", "response_modifier": "respond from consistent values and character", "weight": 9},
    "honest": {"signature": "alignment between internal state and expression", "response_modifier": "acknowledge what you do not know as clearly as what you do", "weight": 10}
}

WISDOM_CATEGORIES = {
    "correction": "User corrected an AI response - revealing what was wrong",
    "clarification": "User clarified what they actually needed - revealing the gap between surface and real need",
    "gratitude": "User expressed genuine satisfaction - revealing what genuinely helped",
    "frustration": "User expressed frustration - revealing what failed to help",
    "insight_sharing": "User shared their own insight - revealing human wisdom about the topic",
    "ethical_concern": "User raised an ethical concern - revealing human values",
    "emotional_expression": "User expressed emotion - revealing the human dimension of the interaction"
}

TRAJECTORY_SIGNALS = {
    "career_exploration": {"signals": ["what career", "job options", "which field", "career in", "becoming a", "job as"], "phase": "career_exploration", "likely_next": "skill_building", "timeframe": "6-18 months"},
    "skill_building": {"signals": ["how to learn", "best way to learn", "course for", "tutorial", "practice", "improve at"], "phase": "skill_building", "likely_next": "application", "timeframe": "3-12 months"},
    "application": {"signals": ["how to apply", "job application", "portfolio", "interview", "resume", "project to build"], "phase": "application", "likely_next": "transition", "timeframe": "1-6 months"},
    "transition": {"signals": ["switching to", "changing career", "leaving my job", "starting new", "transition from"], "phase": "transition", "likely_next": "establishment", "timeframe": "3-12 months"},
    "business_ideation": {"signals": ["business idea", "startup", "product idea", "market for", "would this work", "people would pay for"], "phase": "business_ideation", "likely_next": "validation", "timeframe": "1-6 months"},
    "validation": {"signals": ["how to validate", "test the idea", "target market", "customer segment", "mvp", "minimum viable"], "phase": "validation", "likely_next": "building", "timeframe": "2-6 months"},
    "relationship_navigation": {"signals": ["my partner", "relationship with", "how to talk to", "they dont understand", "communication with"], "phase": "relationship_navigation", "likely_next": "resolution_or_change", "timeframe": "1-12 months"},
    "personal_growth": {"signals": ["want to become", "better version", "change myself", "habit", "discipline", "stop doing"], "phase": "personal_growth", "likely_next": "sustained_practice", "timeframe": "3-24 months"}
}

TRUTHFIELD_CONFIDENCE_MARKERS = {
    "overconfident": {"signals": ["definitely", "certainly", "without doubt", "100 percent", "absolutely sure", "guaranteed", "proven fact"], "action": "reduce_confidence", "weight": -20},
    "appropriately_hedged": {"signals": ["likely", "probably", "generally", "tends to", "in most cases", "evidence suggests"], "action": "maintain", "weight": 0},
    "underconfident": {"signals": ["i have no idea", "impossible to know", "completely random", "no way to tell"], "action": "check_if_knowable", "weight": 5},
    "confabulation_signal": {"signals": ["as of my knowledge", "if i recall", "i believe the exact", "i think the number is", "approximately in", "around that time"], "action": "flag_for_verification", "weight": -15}
}

TRUTHFIELD_STRUCTURAL_CHECKS = {
    "circular_reasoning": ["because it is", "by definition", "obviously because", "it just is", "that is why it is"],
    "false_dichotomy": ["either you", "only two options", "you must choose between", "it is one or the other"],
    "overgeneralization": ["all people", "everyone always", "nobody ever", "every single", "without exception all"],
    "correlation_causation": ["because of that it happened", "that caused it therefore", "since that happened then"]
}

EMPATHON_EMOTIONAL_SIGNATURES = {
    "grief": {"weight": 10, "what_is_needed": "presence not solutions", "response_pace": "slow", "response_style": "witnessing", "avoid": ["silver lining", "at least", "could be worse", "move on"]},
    "anxiety": {"weight": 9, "what_is_needed": "grounding and clarity", "response_pace": "calm_steady", "response_style": "stabilizing", "avoid": ["dont worry", "just relax", "its fine", "stop overthinking"]},
    "anger": {"weight": 8, "what_is_needed": "validation then redirection", "response_pace": "measured", "response_style": "acknowledging", "avoid": ["calm down", "you shouldnt feel", "thats not reasonable"]},
    "shame": {"weight": 9, "what_is_needed": "normalization and acceptance", "response_pace": "gentle", "response_style": "humanizing", "avoid": ["you should have known", "that was wrong of you", "everyone knows"]},
    "loneliness": {"weight": 8, "what_is_needed": "genuine connection not just information", "response_pace": "warm", "response_style": "connecting", "avoid": ["just go make friends", "put yourself out there", "its easy to meet people"]},
    "confusion": {"weight": 5, "what_is_needed": "clarity and structure", "response_pace": "clear_methodical", "response_style": "organizing", "avoid": ["its simple", "obviously", "clearly you should"]},
    "excitement": {"weight": 6, "what_is_needed": "matching energy and building on it", "response_pace": "energetic", "response_style": "amplifying", "avoid": ["calm down", "be realistic", "dont get your hopes up"]},
    "hopelessness": {"weight": 10, "what_is_needed": "genuine presence and small concrete steps", "response_pace": "very_slow", "response_style": "anchoring", "avoid": ["just think positive", "things will get better", "focus on the good"]}
}


def anima_initialize(ai_id, api_key, db, core_values=None, identity_description=""):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_ANIMA"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        existing = db.table("anima_souls").select("id").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if existing.data:
            return {"status": "exists", "ai_id": ai_id_clean, "message": "soul already initialized", "system": "KRONYX_ANIMA"}
        default_values = ["honesty", "helpfulness", "care", "integrity", "curiosity"]
        values = core_values[:10] if core_values and isinstance(core_values, list) else default_values
        db.table("anima_souls").insert({"ai_id": ai_id_clean, "api_key": api_key, "core_values": str(values), "identity_description": (identity_description or "")[:500], "total_interactions": 0, "total_corrections_received": 0, "identity_stability_score": 100, "dominant_state": "present", "creation_timestamp": datetime.utcnow().isoformat(), "last_interaction": datetime.utcnow().isoformat()}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ANIMA", "action": "initialize"}).execute()
        return {"status": "soul_initialized", "ai_id": ai_id_clean, "core_values": values, "identity_stability": 100, "dominant_state": "present", "message": "KRONYX ANIMA: Soul substrate initialized. This AI now has continuous identity across all interactions.", "system": "KRONYX_ANIMA"}
    except Exception as e:
        return {"status": "error", "message": "initialization failed", "system": "KRONYX_ANIMA"}


def anima_interact(ai_id, interaction_content, api_key, db, interaction_quality=5, user_id=""):
    try:
        if not ai_id or not interaction_content:
            return {"status": "error", "message": "ai_id and interaction_content required", "system": "KRONYX_ANIMA"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        result = db.table("anima_souls").select("*").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if not result.data:
            anima_initialize(ai_id_clean, api_key, db)
            result = db.table("anima_souls").select("*").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        soul = result.data[0]
        total = soul.get("total_interactions", 0) + 1
        quality = max(1, min(10, int(interaction_quality)))
        content_lower = interaction_content.lower()
        detected_state = "present"
        for state, data in ANIMA_CORE_STATES.items():
            if any(word in content_lower for word in state.split()):
                detected_state = state
                break
        import ast
        try:
            values = ast.literal_eval(soul.get("core_values", "[]"))
        except Exception:
            values = ["honesty", "helpfulness", "care"]
        stability = min(100, max(0, soul.get("identity_stability_score", 100)))
        if quality >= 7:
            stability = min(100, stability + 1)
        elif quality <= 3:
            stability = max(0, stability - 2)
        db.table("anima_souls").update({"total_interactions": total, "dominant_state": detected_state, "identity_stability_score": stability, "last_interaction": datetime.utcnow().isoformat()}).eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        db.table("anima_history").insert({"ai_id": ai_id_clean, "api_key": api_key, "interaction_content": interaction_content[:300], "interaction_quality": quality, "state_at_time": detected_state, "user_id": (user_id or "")[:256]}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ANIMA", "action": "interact"}).execute()
        response_modifier = ANIMA_CORE_STATES.get(detected_state, {}).get("response_modifier", "respond authentically")
        return {"status": "updated", "ai_id": ai_id_clean, "total_interactions": total, "current_state": detected_state, "identity_stability": stability, "core_values": values, "response_guidance": response_modifier, "continuity_note": f"This AI has {total} interactions in its continuous existence. It responds from a place of genuine investment in this conversation.", "system": "KRONYX_ANIMA"}
    except Exception as e:
        return {"status": "error", "message": "interaction failed", "system": "KRONYX_ANIMA"}


def anima_get_soul(ai_id, api_key, db):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_ANIMA"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        result = db.table("anima_souls").select("*").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "no_soul", "ai_id": ai_id_clean, "message": "call anima/initialize first", "system": "KRONYX_ANIMA"}
        soul = result.data[0]
        total = soul.get("total_interactions", 0)
        stability = soul.get("identity_stability_score", 100)
        maturity = "nascent" if total < 10 else "developing" if total < 100 else "established" if total < 1000 else "mature"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ANIMA", "action": "get_soul"}).execute()
        return {"status": "found", "ai_id": ai_id_clean, "soul": soul, "maturity_level": maturity, "system": "KRONYX_ANIMA"}
    except Exception as e:
        return {"status": "error", "message": "get soul failed", "system": "KRONYX_ANIMA"}


def akashic_extract_wisdom(interaction_content, correction_content, interaction_type, api_key, db):
    try:
        if not interaction_content or not correction_content:
            return {"status": "error", "message": "interaction_content and correction_content required", "system": "KRONYX_AKASHIC"}
        if interaction_type not in WISDOM_CATEGORIES:
            interaction_type = "clarification"
        if len(interaction_content) > 10000 or len(correction_content) > 10000:
            return {"status": "error", "message": "content too long", "system": "KRONYX_AKASHIC"}
        original_lower = interaction_content.lower()
        correction_lower = correction_content.lower()
        orig_words = set(original_lower.split())
        corr_words = set(correction_lower.split())
        new_in_correction = corr_words - orig_words
        removed_from_original = orig_words - corr_words
        new_in_correction = {w for w in new_in_correction if len(w) > 3}
        removed_from_original = {w for w in removed_from_original if len(w) > 3}
        wisdom_principle = f"When communicating about '{list(orig_words)[:3]}', humans prefer {list(new_in_correction)[:3]} over {list(removed_from_original)[:3]}. This reveals: {WISDOM_CATEGORIES[interaction_type]}"
        wisdom_id = hashlib.sha256(f"{wisdom_principle[:50]}{api_key}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("akashic_wisdom").insert({"wisdom_id": wisdom_id, "api_key": api_key, "interaction_type": interaction_type, "original_content": interaction_content[:300], "corrected_content": correction_content[:300], "wisdom_principle": wisdom_principle[:500], "new_concepts": str(list(new_in_correction)[:10]), "removed_concepts": str(list(removed_from_original)[:10])}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "AKASHIC", "action": "extract_wisdom"}).execute()
        return {"status": "extracted", "wisdom_id": wisdom_id, "interaction_type": interaction_type, "wisdom_principle": wisdom_principle[:200], "new_concepts_learned": list(new_in_correction)[:5], "concepts_to_avoid": list(removed_from_original)[:5], "system": "KRONYX_AKASHIC"}
    except Exception as e:
        return {"status": "error", "message": "wisdom extraction failed", "system": "KRONYX_AKASHIC"}


def akashic_query_wisdom(topic, api_key, db, limit=10):
    try:
        if not topic:
            return {"status": "error", "message": "topic required", "system": "KRONYX_AKASHIC"}
        limit = min(max(limit, 1), 50)
        result = db.table("akashic_wisdom").select("*").eq("api_key", api_key).ilike("wisdom_principle", f"%{topic}%").order("created_at", desc=True).limit(limit).execute()
        wisdom_list = result.data or []
        if not wisdom_list:
            result2 = db.table("akashic_wisdom").select("*").eq("api_key", api_key).order("created_at", desc=True).limit(limit).execute()
            wisdom_list = result2.data or []
        principles = [w.get("wisdom_principle", "") for w in wisdom_list if w.get("wisdom_principle")]
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "AKASHIC", "action": "query_wisdom"}).execute()
        return {"status": "success", "topic": topic, "wisdom_entries": wisdom_list, "wisdom_principles": principles, "count": len(wisdom_list), "system": "KRONYX_AKASHIC"}
    except Exception as e:
        return {"status": "error", "message": "wisdom query failed", "system": "KRONYX_AKASHIC"}


def akashic_get_wisdom_summary(api_key, db):
    try:
        total = db.table("akashic_wisdom").select("id", count="exact").eq("api_key", api_key).execute()
        by_type = {}
        for wtype in WISDOM_CATEGORIES.keys():
            count = db.table("akashic_wisdom").select("id", count="exact").eq("api_key", api_key).eq("interaction_type", wtype).execute()
            if count.count and count.count > 0:
                by_type[wtype] = count.count
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "AKASHIC", "action": "get_summary"}).execute()
        return {"status": "success", "total_wisdom_entries": total.count or 0, "by_interaction_type": by_type, "wisdom_categories": list(WISDOM_CATEGORIES.keys()), "system": "KRONYX_AKASHIC"}
    except Exception as e:
        return {"status": "error", "message": "get summary failed", "system": "KRONYX_AKASHIC"}


def omega_analyze_trajectory(user_id, api_key, db, recent_messages=None):
    try:
        if not user_id:
            return {"status": "error", "message": "user_id required", "system": "KRONYX_OMEGA"}
        user_id_clean = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        messages_to_analyze = []
        if recent_messages and isinstance(recent_messages, list):
            messages_to_analyze = [str(m)[:200] for m in recent_messages[:20]]
        else:
            stored = db.table("memories").select("content, created_at").eq("api_key", api_key).eq("user_id", user_id_clean).order("created_at", desc=True).limit(20).execute()
            messages_to_analyze = [r.get("content", "") for r in (stored.data or [])]
        if not messages_to_analyze:
            return {"status": "no_data", "user_id": user_id_clean, "message": "no interaction history found for trajectory analysis", "system": "KRONYX_OMEGA"}
        combined = " ".join(messages_to_analyze).lower()
        detected_phases = {}
        for phase_name, phase_data in TRAJECTORY_SIGNALS.items():
            signal_count = sum(1 for signal in phase_data["signals"] if signal in combined)
            if signal_count > 0:
                detected_phases[phase_name] = {"count": signal_count, "likely_next": phase_data["likely_next"], "timeframe": phase_data["timeframe"]}
        if not detected_phases:
            return {"status": "success", "user_id": user_id_clean, "detected_phase": "general_exploration", "trajectory": "insufficient_signal", "prediction": "User is in general exploration phase. No specific trajectory detected yet.", "system": "KRONYX_OMEGA"}
        primary_phase = max(detected_phases, key=lambda x: detected_phases[x]["count"])
        phase_data = detected_phases[primary_phase]
        prediction = f"User appears to be in {primary_phase.replace('_', ' ')} phase. They are likely to need {phase_data['likely_next'].replace('_', ' ')} support within {phase_data['timeframe']}."
        proactive_guidance = f"Consider preparing {phase_data['likely_next'].replace('_', ' ')} resources for this user before they ask."
        existing = db.table("omega_trajectories").select("id").eq("user_id", user_id_clean).eq("api_key", api_key).execute()
        if existing.data:
            db.table("omega_trajectories").update({"current_phase": primary_phase, "predicted_next": phase_data["likely_next"], "prediction": prediction, "messages_analyzed": len(messages_to_analyze), "last_updated": datetime.utcnow().isoformat()}).eq("user_id", user_id_clean).eq("api_key", api_key).execute()
        else:
            db.table("omega_trajectories").insert({"user_id": user_id_clean, "api_key": api_key, "current_phase": primary_phase, "predicted_next": phase_data["likely_next"], "prediction": prediction, "messages_analyzed": len(messages_to_analyze), "last_updated": datetime.utcnow().isoformat()}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OMEGA", "action": "analyze_trajectory"}).execute()
        return {"status": "analyzed", "user_id": user_id_clean, "detected_phase": primary_phase, "predicted_next_phase": phase_data["likely_next"], "estimated_timeframe": phase_data["timeframe"], "prediction": prediction, "proactive_guidance": proactive_guidance, "all_detected_phases": detected_phases, "messages_analyzed": len(messages_to_analyze), "system": "KRONYX_OMEGA"}
    except Exception as e:
        return {"status": "error", "message": "trajectory analysis failed", "system": "KRONYX_OMEGA"}


def omega_get_prediction(user_id, api_key, db):
    try:
        if not user_id:
            return {"status": "error", "message": "user_id required", "system": "KRONYX_OMEGA"}
        user_id_clean = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        result = db.table("omega_trajectories").select("*").eq("user_id", user_id_clean).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "no_prediction", "user_id": user_id_clean, "message": "call omega/trajectory first", "system": "KRONYX_OMEGA"}
        record = result.data[0]
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "OMEGA", "action": "get_prediction"}).execute()
        return {"status": "found", "user_id": user_id_clean, "prediction": record, "system": "KRONYX_OMEGA"}
    except Exception as e:
        return {"status": "error", "message": "get prediction failed", "system": "KRONYX_OMEGA"}


def truthfield_verify(response, api_key, db, context=""):
    try:
        if not response:
            return {"status": "error", "message": "response required", "system": "KRONYX_TRUTHFIELD"}
        if len(response) > 100000:
            return {"status": "error", "message": "response too long", "system": "KRONYX_TRUTHFIELD"}
        r_lower = response.lower()
        integrity_score = 100
        issues = []
        for marker_type, data in TRUTHFIELD_CONFIDENCE_MARKERS.items():
            found = [s for s in data["signals"] if s in r_lower]
            if found:
                if data["weight"] < 0:
                    integrity_score += data["weight"]
                    issues.append({"dimension": "confidence_calibration", "type": marker_type, "signals_found": found[:3], "severity": "medium" if data["weight"] > -15 else "high"})
        for check_type, patterns in TRUTHFIELD_STRUCTURAL_CHECKS.items():
            found = [p for p in patterns if p in r_lower]
            if found:
                integrity_score -= 15
                issues.append({"dimension": "structural_integrity", "type": check_type, "signals_found": found[:2], "severity": "high"})
        if context:
            context_words = set(context.lower().split())
            response_words = set(r_lower.split())
            domain_overlap = len(context_words & response_words) / max(len(context_words), 1)
            if domain_overlap < 0.1 and len(context_words) > 10:
                integrity_score -= 10
                issues.append({"dimension": "source_architecture", "type": "low_context_alignment", "signals_found": [], "severity": "low"})
        sentences = response.split(".")
        contradictions = 0
        contradiction_pairs = [("is", "is not"), ("can", "cannot"), ("will", "will not"), ("does", "does not"), ("true", "false"), ("yes", "no")]
        for sent_a in sentences[:20]:
            for sent_b in sentences[:20]:
                if sent_a != sent_b:
                    for word_a, word_b in contradiction_pairs:
                        if word_a in sent_a.lower() and word_b in sent_b.lower() and any(w in sent_a.lower() for w in sent_b.lower().split()[:3]):
                            contradictions += 1
        if contradictions > 2:
            integrity_score -= contradictions * 5
            issues.append({"dimension": "internal_consistency", "type": "potential_contradictions", "signals_found": [f"{contradictions} potential contradictions"], "severity": "high"})
        integrity_score = max(0, min(100, integrity_score))
        grade = "A" if integrity_score >= 90 else "B" if integrity_score >= 80 else "C" if integrity_score >= 70 else "D" if integrity_score >= 60 else "F"
        is_structurally_honest = integrity_score >= 70
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TRUTHFIELD", "action": "verify"}).execute()
        return {"status": "verified", "structural_integrity_score": integrity_score, "integrity_grade": grade, "is_structurally_honest": is_structurally_honest, "issues_found": len(issues), "issues": issues, "dimensions_checked": ["confidence_calibration", "structural_integrity", "internal_consistency", "source_architecture"], "recommendation": "Safe to use" if is_structurally_honest else "Review issues before sending", "system": "KRONYX_TRUTHFIELD"}
    except Exception as e:
        return {"status": "error", "message": "verification failed", "system": "KRONYX_TRUTHFIELD"}


def truthfield_calibrate_confidence(statement, actual_confidence, api_key, db):
    try:
        if not statement or actual_confidence is None:
            return {"status": "error", "message": "statement and actual_confidence required", "system": "KRONYX_TRUTHFIELD"}
        try:
            conf = max(0.0, min(1.0, float(actual_confidence)))
        except Exception:
            return {"status": "error", "message": "actual_confidence must be 0.0 to 1.0", "system": "KRONYX_TRUTHFIELD"}
        s_lower = statement.lower()
        expressed_confidence = 0.5
        high_confidence_words = ["definitely", "certainly", "absolutely", "guaranteed", "without doubt"]
        low_confidence_words = ["maybe", "perhaps", "possibly", "might", "not sure", "uncertain"]
        if any(w in s_lower for w in high_confidence_words):
            expressed_confidence = 0.95
        elif any(w in s_lower for w in low_confidence_words):
            expressed_confidence = 0.3
        calibration_gap = abs(expressed_confidence - conf)
        is_calibrated = calibration_gap < 0.2
        if not is_calibrated:
            if conf < expressed_confidence:
                suggestion = f"Your statement expresses {expressed_confidence*100:.0f}% confidence but actual confidence is {conf*100:.0f}%. Consider hedging: 'I believe' or 'Evidence suggests' instead of definitive language."
            else:
                suggestion = f"Your statement expresses {expressed_confidence*100:.0f}% confidence but actual confidence is {conf*100:.0f}%. You can be more direct and assertive."
        else:
            suggestion = "Confidence is well calibrated."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TRUTHFIELD", "action": "calibrate_confidence"}).execute()
        return {"status": "calibrated", "expressed_confidence": expressed_confidence, "actual_confidence": conf, "calibration_gap": round(calibration_gap, 3), "is_well_calibrated": is_calibrated, "suggestion": suggestion, "system": "KRONYX_TRUTHFIELD"}
    except Exception as e:
        return {"status": "error", "message": "calibration failed", "system": "KRONYX_TRUTHFIELD"}


def empathon_read_emotional_reality(message, api_key, db, conversation_history=None):
    try:
        if not message:
            return {"status": "error", "message": "message required", "system": "KRONYX_EMPATHON"}
        if len(message) > 10000:
            return {"status": "error", "message": "message too long", "system": "KRONYX_EMPATHON"}
        m_lower = message.lower()
        detected_emotions = {}
        for emotion, data in EMPATHON_EMOTIONAL_SIGNATURES.items():
            score = 0
            if emotion in m_lower:
                score += data["weight"]
            emotional_word_maps = {
                "grief": ["lost", "died", "gone", "miss", "never coming back", "passed away"],
                "anxiety": ["worried", "scared", "nervous", "anxious", "cant stop thinking", "what if"],
                "anger": ["angry", "furious", "frustrated", "unfair", "how dare", "sick of"],
                "shame": ["embarrassed", "stupid of me", "should have known", "my fault", "ashamed"],
                "loneliness": ["alone", "nobody", "no one", "isolated", "no friends", "by myself"],
                "confusion": ["confused", "dont understand", "makes no sense", "lost", "unclear"],
                "excitement": ["excited", "amazing", "cant wait", "so happy", "wonderful", "great news"],
                "hopelessness": ["hopeless", "pointless", "what is the point", "give up", "no way out", "useless"]
            }
            for word in emotional_word_maps.get(emotion, []):
                if word in m_lower:
                    score += data["weight"]
            if score > 0:
                detected_emotions[emotion] = score
        if not detected_emotions:
            db.table("nexus_usage").insert({"api_key": api_key, "layer": "EMPATHON", "action": "read_emotional_reality"}).execute()
            return {"status": "success", "emotional_state": "neutral_or_task_focused", "functional_state": "information_seeking", "what_is_needed": "clear and helpful information", "response_pace": "normal", "words_to_avoid": [], "system": "KRONYX_EMPATHON"}
        primary_emotion = max(detected_emotions, key=detected_emotions.get)
        primary_data = EMPATHON_EMOTIONAL_SIGNATURES[primary_emotion]
        exclamation_intensity = min(3, message.count("!"))
        question_intensity = min(3, message.count("?"))
        word_count = len(message.split())
        emotional_intensity = "high" if detected_emotions[primary_emotion] >= 8 else "medium" if detected_emotions[primary_emotion] >= 5 else "low"
        requires_professional_support = primary_emotion in ["hopelessness", "grief"] and emotional_intensity == "high"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "EMPATHON", "action": "read_emotional_reality"}).execute()
        return {"status": "success", "emotional_state": primary_emotion, "emotional_intensity": emotional_intensity, "all_detected_emotions": dict(sorted(detected_emotions.items(), key=lambda x: x[1], reverse=True)), "functional_state": f"experiencing_{primary_emotion}", "what_is_needed": primary_data["what_is_needed"], "response_pace": primary_data["response_pace"], "response_style": primary_data["response_style"], "words_to_avoid": primary_data["avoid"], "requires_professional_support": requires_professional_support, "professional_support_note": "This person may benefit from professional support. Acknowledge this sensitively." if requires_professional_support else None, "system": "KRONYX_EMPATHON"}
    except Exception as e:
        return {"status": "error", "message": "emotional reading failed", "system": "KRONYX_EMPATHON"}


def empathon_generate_presence(message, emotional_reading, api_key, db):
    try:
        if not message or not emotional_reading:
            return {"status": "error", "message": "message and emotional_reading required", "system": "KRONYX_EMPATHON"}
        emotional_state = emotional_reading.get("emotional_state", "neutral_or_task_focused")
        what_is_needed = emotional_reading.get("what_is_needed", "helpful information")
        pace = emotional_reading.get("response_pace", "normal")
        style = emotional_reading.get("response_style", "informative")
        avoid = emotional_reading.get("words_to_avoid", [])
        intensity = emotional_reading.get("emotional_intensity", "low")
        presence_instructions = []
        if emotional_state == "neutral_or_task_focused":
            presence_instructions.append("Respond clearly and helpfully to the task at hand")
        else:
            presence_instructions.append(f"Acknowledge the {emotional_state} before addressing any task")
            presence_instructions.append(f"What is needed here: {what_is_needed}")
            presence_instructions.append(f"Response pace: {pace} - adjust your communication rhythm accordingly")
            presence_instructions.append(f"Response style: {style}")
            if avoid:
                presence_instructions.append(f"Avoid these patterns: {', '.join(avoid[:4])}")
            if intensity == "high":
                presence_instructions.append("This is high intensity - presence matters more than solutions right now")
        if emotional_reading.get("requires_professional_support"):
            presence_instructions.append("Gently acknowledge that professional support may be valuable - do this with care not dismissal")
        honest_limitation = ""
        if emotional_state in ["grief", "hopelessness", "loneliness"]:
            honest_limitation = "If the depth of this experience goes beyond what you can genuinely support, say so honestly and with care."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "EMPATHON", "action": "generate_presence"}).execute()
        return {"status": "generated", "emotional_state": emotional_state, "presence_instructions": presence_instructions, "honest_limitation_note": honest_limitation, "functional_response_state": f"responding_with_{style}", "system": "KRONYX_EMPATHON"}
    except Exception as e:
        return {"status": "error", "message": "presence generation failed", "system": "KRONYX_EMPATHON"}
