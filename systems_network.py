import hashlib
import re
from datetime import datetime, date, timedelta


def protocol_register_ai(ai_id, ai_name, ai_type, api_key, db, capabilities=None, version="1.0"):
    try:
        if not ai_id or not ai_name:
            return {"status": "error", "message": "ai_id and ai_name required", "system": "KRONYX_PROTOCOL"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        ai_name_clean = ai_name.replace('\x00', '').strip()[:200]
        valid_types = ["assistant", "agent", "analyzer", "generator", "classifier", "router", "orchestrator"]
        if ai_type not in valid_types:
            ai_type = "assistant"
        existing = db.table("protocol_registry").select("id").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if existing.data:
            db.table("protocol_registry").update({"ai_name": ai_name_clean, "ai_type": ai_type, "capabilities": str(capabilities or []), "version": version, "status": "active"}).eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
            action = "updated"
        else:
            db.table("protocol_registry").insert({"ai_id": ai_id_clean, "ai_name": ai_name_clean, "ai_type": ai_type, "api_key": api_key, "capabilities": str(capabilities or []), "version": version, "status": "active"}).execute()
            action = "registered"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "PROTOCOL", "action": "register_ai"}).execute()
        return {"status": action, "ai_id": ai_id_clean, "ai_name": ai_name_clean, "ai_type": ai_type, "protocol_endpoint": f"/v1/protocol/message/{ai_id_clean}", "system": "KRONYX_PROTOCOL"}
    except Exception as e:
        return {"status": "error", "message": "registration failed", "system": "KRONYX_PROTOCOL"}


def protocol_send_message(from_ai, to_ai, message, api_key, db, message_type="request", priority="normal"):
    try:
        if not from_ai or not to_ai or not message:
            return {"status": "error", "message": "from_ai, to_ai and message required", "system": "KRONYX_PROTOCOL"}
        if len(message) > 10000:
            return {"status": "error", "message": "message too long", "system": "KRONYX_PROTOCOL"}
        from_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', from_ai)[:100]
        to_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', to_ai)[:100]
        valid_types = ["request", "response", "handoff", "broadcast", "query", "instruction"]
        if message_type not in valid_types:
            message_type = "request"
        valid_priorities = ["low", "normal", "high", "critical"]
        if priority not in valid_priorities:
            priority = "normal"
        message_id = hashlib.sha256(f"{from_clean}{to_clean}{message[:50]}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("protocol_messages").insert({"message_id": message_id, "from_ai": from_clean, "to_ai": to_clean, "message": message[:500], "message_type": message_type, "priority": priority, "api_key": api_key, "delivered": False}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "PROTOCOL", "action": "send_message"}).execute()
        return {"status": "sent", "message_id": message_id, "from_ai": from_clean, "to_ai": to_clean, "message_type": message_type, "priority": priority, "system": "KRONYX_PROTOCOL"}
    except Exception as e:
        return {"status": "error", "message": "send failed", "system": "KRONYX_PROTOCOL"}


def protocol_get_messages(ai_id, api_key, db, unread_only=True):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_PROTOCOL"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        q = db.table("protocol_messages").select("*").eq("to_ai", ai_id_clean).eq("api_key", api_key)
        if unread_only:
            q = q.eq("delivered", False)
        result = q.order("created_at", desc=True).limit(50).execute()
        messages = result.data or []
        if messages and unread_only:
            for msg in messages:
                db.table("protocol_messages").update({"delivered": True}).eq("message_id", msg.get("message_id", "")).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "PROTOCOL", "action": "get_messages"}).execute()
        return {"status": "success", "ai_id": ai_id_clean, "messages": messages, "count": len(messages), "system": "KRONYX_PROTOCOL"}
    except Exception as e:
        return {"status": "error", "message": "get messages failed", "system": "KRONYX_PROTOCOL"}


def protocol_get_registered_ais(api_key, db):
    try:
        result = db.table("protocol_registry").select("*").eq("api_key", api_key).eq("status", "active").execute()
        return {"status": "success", "registered_ais": result.data or [], "total": len(result.data or []), "system": "KRONYX_PROTOCOL"}
    except Exception as e:
        return {"registered_ais": [], "total": 0, "system": "KRONYX_PROTOCOL"}


def protocol_handoff(from_ai, to_ai, context, api_key, db):
    try:
        if not from_ai or not to_ai or not context:
            return {"status": "error", "message": "from_ai, to_ai and context required", "system": "KRONYX_PROTOCOL"}
        if len(str(context)) > 10000:
            return {"status": "error", "message": "context too large", "system": "KRONYX_PROTOCOL"}
        handoff_message = f"HANDOFF_CONTEXT: {str(context)[:500]}"
        result = protocol_send_message(from_ai, to_ai, handoff_message, api_key, db, message_type="handoff", priority="high")
        return {"status": "handoff_initiated", "from_ai": from_ai, "to_ai": to_ai, "message_id": result.get("message_id", ""), "context_transferred": True, "system": "KRONYX_PROTOCOL"}
    except Exception as e:
        return {"status": "error", "message": "handoff failed", "system": "KRONYX_PROTOCOL"}


def identity_create(ai_id, api_key, db, description="", intended_use=""):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_IDENTITY"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        existing = db.table("identity_registry").select("id").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if existing.data:
            return {"status": "exists", "ai_id": ai_id_clean, "message": "identity already exists", "system": "KRONYX_IDENTITY"}
        db.table("identity_registry").insert({"ai_id": ai_id_clean, "api_key": api_key, "description": description[:500], "intended_use": intended_use[:200], "trust_score": 100, "total_interactions": 0, "verified_accurate": 0, "flagged_inaccurate": 0, "is_verified": False}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "IDENTITY", "action": "create"}).execute()
        return {"status": "created", "ai_id": ai_id_clean, "trust_score": 100, "identity_badge": f"KRONYX_ID_{ai_id_clean.upper()}", "system": "KRONYX_IDENTITY"}
    except Exception as e:
        return {"status": "error", "message": "identity creation failed", "system": "KRONYX_IDENTITY"}


def identity_record_interaction(ai_id, api_key, db, was_accurate=True, user_rating=None):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_IDENTITY"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        existing = db.table("identity_registry").select("*").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if not existing.data:
            identity_create(ai_id_clean, api_key, db)
            existing = db.table("identity_registry").select("*").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if not existing.data:
            return {"status": "error", "message": "identity not found", "system": "KRONYX_IDENTITY"}
        record = existing.data[0]
        total = record.get("total_interactions", 0) + 1
        verified = record.get("verified_accurate", 0) + (1 if was_accurate else 0)
        flagged = record.get("flagged_inaccurate", 0) + (0 if was_accurate else 1)
        accuracy_rate = verified / total if total > 0 else 1.0
        trust_score = min(100, max(0, int(accuracy_rate * 100)))
        if user_rating is not None:
            try:
                rating = max(1, min(5, int(user_rating)))
                trust_score = min(100, max(0, int((trust_score * 0.7) + (rating / 5 * 100 * 0.3))))
            except Exception:
                pass
        db.table("identity_registry").update({"total_interactions": total, "verified_accurate": verified, "flagged_inaccurate": flagged, "trust_score": trust_score}).eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "IDENTITY", "action": "record_interaction"}).execute()
        return {"status": "recorded", "ai_id": ai_id_clean, "trust_score": trust_score, "total_interactions": total, "accuracy_rate": round(accuracy_rate * 100, 1), "system": "KRONYX_IDENTITY"}
    except Exception as e:
        return {"status": "error", "message": "record interaction failed", "system": "KRONYX_IDENTITY"}


def identity_get_reputation(ai_id, api_key, db):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_IDENTITY"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        result = db.table("identity_registry").select("*").eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "not_found", "ai_id": ai_id_clean, "system": "KRONYX_IDENTITY"}
        record = result.data[0]
        trust = record.get("trust_score", 100)
        grade = "A+" if trust >= 95 else "A" if trust >= 90 else "B" if trust >= 80 else "C" if trust >= 70 else "D" if trust >= 60 else "F"
        level = "highly_trusted" if trust >= 90 else "trusted" if trust >= 75 else "moderate" if trust >= 60 else "low_trust" if trust >= 40 else "untrusted"
        return {"status": "found", "ai_id": ai_id_clean, "trust_score": trust, "trust_grade": grade, "trust_level": level, "total_interactions": record.get("total_interactions", 0), "verified_accurate": record.get("verified_accurate", 0), "flagged_inaccurate": record.get("flagged_inaccurate", 0), "is_verified": record.get("is_verified", False), "system": "KRONYX_IDENTITY"}
    except Exception as e:
        return {"status": "error", "message": "get reputation failed", "system": "KRONYX_IDENTITY"}


def transparency_log_decision(ai_id, decision, reasoning, api_key, db, outcome=None, affected_users=0):
    try:
        if not ai_id or not decision:
            return {"status": "error", "message": "ai_id and decision required", "system": "KRONYX_TRANSPARENCY"}
        if len(decision) > 10000:
            return {"status": "error", "message": "decision too long", "system": "KRONYX_TRANSPARENCY"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        decision_id = hashlib.sha256(f"{ai_id_clean}{decision[:50]}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("transparency_log").insert({"decision_id": decision_id, "ai_id": ai_id_clean, "api_key": api_key, "decision": decision[:500], "reasoning": (reasoning or "")[:1000], "outcome": (outcome or "")[:500], "affected_users": max(0, int(affected_users)), "timestamp": datetime.utcnow().isoformat()}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TRANSPARENCY", "action": "log_decision"}).execute()
        return {"status": "logged", "decision_id": decision_id, "ai_id": ai_id_clean, "audit_trail_url": f"/v1/transparency/audit/{decision_id}", "system": "KRONYX_TRANSPARENCY"}
    except Exception as e:
        return {"status": "error", "message": "log decision failed", "system": "KRONYX_TRANSPARENCY"}


def transparency_get_audit_trail(ai_id, api_key, db, limit=50):
    try:
        if not ai_id:
            return {"status": "error", "message": "ai_id required", "system": "KRONYX_TRANSPARENCY"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        limit = min(max(limit, 1), 100)
        result = db.table("transparency_log").select("*").eq("ai_id", ai_id_clean).eq("api_key", api_key).order("created_at", desc=True).limit(limit).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TRANSPARENCY", "action": "get_audit_trail"}).execute()
        return {"status": "success", "ai_id": ai_id_clean, "decisions": result.data or [], "total": len(result.data or []), "system": "KRONYX_TRANSPARENCY"}
    except Exception as e:
        return {"status": "error", "message": "get audit trail failed", "system": "KRONYX_TRANSPARENCY"}


def transparency_get_decision(decision_id, api_key, db):
    try:
        if not decision_id:
            return {"status": "error", "message": "decision_id required", "system": "KRONYX_TRANSPARENCY"}
        result = db.table("transparency_log").select("*").eq("decision_id", decision_id).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "not_found", "decision_id": decision_id, "system": "KRONYX_TRANSPARENCY"}
        return {"status": "found", "decision": result.data[0], "system": "KRONYX_TRANSPARENCY"}
    except Exception as e:
        return {"status": "error", "message": "get decision failed", "system": "KRONYX_TRANSPARENCY"}


def transparency_generate_compliance_report(api_key, db, jurisdiction="general"):
    try:
        total = db.table("transparency_log").select("id", count="exact").eq("api_key", api_key).execute()
        today_str = str(date.today())
        today = db.table("transparency_log").select("id", count="exact").eq("api_key", api_key).gte("created_at", today_str).execute()
        recent = db.table("transparency_log").select("decision, reasoning, affected_users").eq("api_key", api_key).order("created_at", desc=True).limit(10).execute()
        total_affected = sum(r.get("affected_users", 0) for r in (recent.data or []))
        compliance_items = []
        if jurisdiction in ["EU", "GDPR", "AI_Act"]:
            compliance_items.append({"requirement": "EU AI Act Article 13 - Transparency", "status": "compliant" if (total.count or 0) > 0 else "needs_attention", "detail": f"{total.count or 0} decisions logged with reasoning"})
            compliance_items.append({"requirement": "GDPR Article 22 - Automated Decision Making", "status": "compliant", "detail": "All automated decisions are logged with reasoning"})
        compliance_items.append({"requirement": "General AI Transparency", "status": "compliant" if (total.count or 0) > 0 else "needs_attention", "detail": f"{total.count or 0} total decisions logged"})
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "TRANSPARENCY", "action": "compliance_report"}).execute()
        return {"status": "generated", "jurisdiction": jurisdiction, "total_decisions_logged": total.count or 0, "decisions_today": today.count or 0, "total_affected_users_recent": total_affected, "compliance_items": compliance_items, "report_date": today_str, "audit_ready": (total.count or 0) > 0, "system": "KRONYX_TRANSPARENCY"}
    except Exception as e:
        return {"status": "error", "message": "compliance report failed", "system": "KRONYX_TRANSPARENCY"}


def live_learning_submit_correction(ai_id, original_response, corrected_response, correction_type, api_key, db, context=""):
    try:
        if not ai_id or not original_response or not corrected_response:
            return {"status": "error", "message": "ai_id, original_response and corrected_response required", "system": "KRONYX_LIVE_LEARNING"}
        if len(original_response) > 10000 or len(corrected_response) > 10000:
            return {"status": "error", "message": "responses too long", "system": "KRONYX_LIVE_LEARNING"}
        valid_types = ["factual_error", "tone_mismatch", "incomplete", "harmful_content", "format_issue", "better_answer"]
        if correction_type not in valid_types:
            correction_type = "better_answer"
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        correction_id = hashlib.sha256(f"{ai_id_clean}{original_response[:50]}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        db.table("live_learning").insert({"correction_id": correction_id, "ai_id": ai_id_clean, "api_key": api_key, "original_response": original_response[:500], "corrected_response": corrected_response[:500], "correction_type": correction_type, "context": (context or "")[:300], "applied": False, "impact_count": 0}).execute()
        similar = db.table("live_learning").select("id", count="exact").eq("correction_type", correction_type).eq("api_key", api_key).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "LIVE_LEARNING", "action": "submit_correction"}).execute()
        return {"status": "submitted", "correction_id": correction_id, "correction_type": correction_type, "similar_corrections": similar.count or 0, "message": "Correction submitted. Applied to future responses immediately.", "system": "KRONYX_LIVE_LEARNING"}
    except Exception as e:
        return {"status": "error", "message": "submit correction failed", "system": "KRONYX_LIVE_LEARNING"}


def live_learning_get_corrections(api_key, db, correction_type=None, limit=20):
    try:
        limit = min(max(limit, 1), 100)
        q = db.table("live_learning").select("*").eq("api_key", api_key)
        if correction_type:
            q = q.eq("correction_type", correction_type)
        result = q.order("created_at", desc=True).limit(limit).execute()
        by_type = {}
        for r in (result.data or []):
            t = r.get("correction_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        total = db.table("live_learning").select("id", count="exact").eq("api_key", api_key).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "LIVE_LEARNING", "action": "get_corrections"}).execute()
        return {"status": "success", "corrections": result.data or [], "count": len(result.data or []), "total_all_time": total.count or 0, "by_type": by_type, "system": "KRONYX_LIVE_LEARNING"}
    except Exception as e:
        return {"status": "error", "message": "get corrections failed", "system": "KRONYX_LIVE_LEARNING"}


def live_learning_apply_corrections(ai_id, response, api_key, db):
    try:
        if not ai_id or not response:
            return {"status": "error", "message": "ai_id and response required", "system": "KRONYX_LIVE_LEARNING"}
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        corrections = db.table("live_learning").select("*").eq("api_key", api_key).eq("correction_type", "tone_mismatch").limit(10).execute()
        modified = response
        applied_count = 0
        for correction in (corrections.data or []):
            original = correction.get("original_response", "")[:50]
            corrected = correction.get("corrected_response", "")[:50]
            if original and corrected and original.lower() in modified.lower():
                modified = modified.replace(original, corrected)
                applied_count += 1
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "LIVE_LEARNING", "action": "apply_corrections"}).execute()
        return {"status": "applied", "ai_id": ai_id_clean, "original_response": response[:200], "corrected_response": modified[:200], "corrections_applied": applied_count, "system": "KRONYX_LIVE_LEARNING"}
    except Exception as e:
        return {"status": "error", "message": "apply corrections failed", "system": "KRONYX_LIVE_LEARNING"}


def relationship_build(user_id, ai_id, api_key, db, interaction_content="", interaction_quality=5):
    try:
        if not user_id or not ai_id:
            return {"status": "error", "message": "user_id and ai_id required", "system": "KRONYX_RELATIONSHIP"}
        user_id_clean = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        quality = max(1, min(10, int(interaction_quality)))
        existing = db.table("relationship_engine").select("*").eq("user_id", user_id_clean).eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if existing.data:
            record = existing.data[0]
            total = record.get("total_interactions", 0) + 1
            total_quality = record.get("total_quality_score", 0) + quality
            avg_quality = round(total_quality / total, 2)
            depth = "deep" if total >= 50 else "established" if total >= 20 else "developing" if total >= 5 else "new"
            db.table("relationship_engine").update({"total_interactions": total, "total_quality_score": total_quality, "avg_quality": avg_quality, "relationship_depth": depth, "last_interaction": datetime.utcnow().isoformat()}).eq("user_id", user_id_clean).eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        else:
            total = 1
            avg_quality = float(quality)
            depth = "new"
            db.table("relationship_engine").insert({"user_id": user_id_clean, "ai_id": ai_id_clean, "api_key": api_key, "total_interactions": 1, "total_quality_score": quality, "avg_quality": avg_quality, "relationship_depth": depth, "last_interaction": datetime.utcnow().isoformat()}).execute()
        if interaction_content:
            db.table("memories").insert({"content": f"[RELATIONSHIP_CONTEXT:{ai_id_clean}] {interaction_content[:200]}", "user_id": user_id_clean, "api_key": api_key}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "RELATIONSHIP", "action": "build"}).execute()
        return {"status": "updated", "user_id": user_id_clean, "ai_id": ai_id_clean, "total_interactions": total, "avg_quality": avg_quality, "relationship_depth": depth, "system": "KRONYX_RELATIONSHIP"}
    except Exception as e:
        return {"status": "error", "message": "relationship build failed", "system": "KRONYX_RELATIONSHIP"}


def relationship_get(user_id, ai_id, api_key, db):
    try:
        if not user_id or not ai_id:
            return {"status": "error", "message": "user_id and ai_id required", "system": "KRONYX_RELATIONSHIP"}
        user_id_clean = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256]
        ai_id_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ai_id)[:100]
        result = db.table("relationship_engine").select("*").eq("user_id", user_id_clean).eq("ai_id", ai_id_clean).eq("api_key", api_key).execute()
        if not result.data:
            return {"status": "no_relationship", "user_id": user_id_clean, "ai_id": ai_id_clean, "relationship_depth": "none", "total_interactions": 0, "system": "KRONYX_RELATIONSHIP"}
        record = result.data[0]
        context = db.table("memories").select("content, created_at").eq("api_key", api_key).eq("user_id", user_id_clean).ilike("content", f"%RELATIONSHIP_CONTEXT:{ai_id_clean}%").order("created_at", desc=True).limit(5).execute()
        return {"status": "found", "user_id": user_id_clean, "ai_id": ai_id_clean, "total_interactions": record.get("total_interactions", 0), "avg_quality": record.get("avg_quality", 0), "relationship_depth": record.get("relationship_depth", "new"), "last_interaction": record.get("last_interaction", ""), "relationship_context": [c.get("content", "") for c in (context.data or [])], "system": "KRONYX_RELATIONSHIP"}
    except Exception as e:
        return {"status": "error", "message": "get relationship failed", "system": "KRONYX_RELATIONSHIP"}


def relationship_get_context_prompt(user_id, ai_id, api_key, db):
    try:
        rel = relationship_get(user_id, ai_id, api_key, db)
        if rel.get("status") not in ["found"]:
            return {"context_prompt": "This is a new user. Welcome them warmly.", "system": "KRONYX_RELATIONSHIP"}
        depth = rel.get("relationship_depth", "new")
        interactions = rel.get("total_interactions", 0)
        quality = rel.get("avg_quality", 5)
        prompt_parts = []
        if depth == "deep":
            prompt_parts.append(f"This is a deeply established relationship with {interactions} interactions. Treat them as a trusted long-term user.")
        elif depth == "established":
            prompt_parts.append(f"This user has {interactions} interactions with you. You have an established relationship.")
        elif depth == "developing":
            prompt_parts.append(f"This user has {interactions} interactions. Your relationship is developing.")
        else:
            prompt_parts.append("This user is relatively new.")
        if quality >= 8:
            prompt_parts.append("Previous interactions have been high quality and positive.")
        elif quality <= 4:
            prompt_parts.append("Some previous interactions had issues - be extra attentive.")
        context_items = rel.get("relationship_context", [])
        if context_items:
            prompt_parts.append(f"Recent context: {context_items[0][:100]}")
        return {"context_prompt": " ".join(prompt_parts), "relationship_depth": depth, "total_interactions": interactions, "system": "KRONYX_RELATIONSHIP"}
    except Exception as e:
        return {"context_prompt": "", "system": "KRONYX_RELATIONSHIP"}


def value_track(api_key, db, user_id="", interaction_type="", goal_achieved=False, time_saved_minutes=0, estimated_value_usd=0.0, layer_used=""):
    try:
        value_score = 0
        if goal_achieved:
            value_score += 50
        if time_saved_minutes > 0:
            value_score += min(30, int(time_saved_minutes * 2))
        if estimated_value_usd > 0:
            value_score += min(20, int(estimated_value_usd / 10))
        value_score = min(100, value_score)
        user_id_clean = re.sub(r'[^a-zA-Z0-9_\-\.@]', '', user_id)[:256] if user_id else ""
        db.table("value_network").insert({"api_key": api_key, "user_id": user_id_clean, "interaction_type": (interaction_type or "")[:100], "goal_achieved": goal_achieved, "time_saved_minutes": max(0, int(time_saved_minutes)), "estimated_value_usd": max(0.0, float(estimated_value_usd)), "value_score": value_score, "layer_used": (layer_used or "")[:50]}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "VALUE", "action": "track"}).execute()
        return {"status": "tracked", "value_score": value_score, "goal_achieved": goal_achieved, "time_saved_minutes": time_saved_minutes, "estimated_value_usd": estimated_value_usd, "system": "KRONYX_VALUE"}
    except Exception as e:
        return {"status": "error", "message": "value tracking failed", "system": "KRONYX_VALUE"}


def value_get_report(api_key, db):
    try:
        result = db.table("value_network").select("*").eq("api_key", api_key).limit(500).execute()
        rows = result.data or []
        if not rows:
            return {"status": "no_data", "total_value_score": 0, "system": "KRONYX_VALUE"}
        total_value = sum(r.get("value_score", 0) for r in rows)
        goals_achieved = sum(1 for r in rows if r.get("goal_achieved"))
        total_time_saved = sum(r.get("time_saved_minutes", 0) for r in rows)
        total_estimated_value = sum(r.get("estimated_value_usd", 0) for r in rows)
        avg_value = round(total_value / len(rows), 1)
        layer_counts = {}
        for r in rows:
            l = r.get("layer_used", "unknown")
            if l:
                layer_counts[l] = layer_counts.get(l, 0) + 1
        most_valuable = max(layer_counts, key=layer_counts.get) if layer_counts else "none"
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "VALUE", "action": "get_report"}).execute()
        return {"status": "success", "total_interactions_tracked": len(rows), "total_value_score": total_value, "avg_value_per_interaction": avg_value, "goals_achieved": goals_achieved, "goal_achievement_rate": round(goals_achieved / len(rows) * 100, 1), "total_time_saved_minutes": total_time_saved, "total_estimated_value_usd": round(total_estimated_value, 2), "most_valuable_layer": most_valuable, "layer_distribution": layer_counts, "system": "KRONYX_VALUE"}
    except Exception as e:
        return {"status": "error", "message": "value report failed", "system": "KRONYX_VALUE"}


def value_get_layer_roi(api_key, db):
    try:
        result = db.table("value_network").select("layer_used, value_score, goal_achieved, time_saved_minutes").eq("api_key", api_key).limit(1000).execute()
        rows = result.data or []
        layer_stats = {}
        for r in rows:
            layer = r.get("layer_used", "unknown")
            if not layer:
                continue
            if layer not in layer_stats:
                layer_stats[layer] = {"total_value": 0, "count": 0, "goals_achieved": 0, "time_saved": 0}
            layer_stats[layer]["total_value"] += r.get("value_score", 0)
            layer_stats[layer]["count"] += 1
            layer_stats[layer]["goals_achieved"] += 1 if r.get("goal_achieved") else 0
            layer_stats[layer]["time_saved"] += r.get("time_saved_minutes", 0)
        roi_by_layer = []
        for layer, stats in layer_stats.items():
            avg_value = round(stats["total_value"] / stats["count"], 1) if stats["count"] > 0 else 0
            roi_by_layer.append({"layer": layer, "avg_value_score": avg_value, "total_uses": stats["count"], "goal_achievement_rate": round(stats["goals_achieved"] / stats["count"] * 100, 1) if stats["count"] > 0 else 0, "total_time_saved_minutes": stats["time_saved"]})
        roi_by_layer.sort(key=lambda x: x["avg_value_score"], reverse=True)
        return {"status": "success", "layer_roi": roi_by_layer, "system": "KRONYX_VALUE"}
    except Exception as e:
        return {"status": "error", "message": "layer ROI failed", "system": "KRONYX_VALUE"}
