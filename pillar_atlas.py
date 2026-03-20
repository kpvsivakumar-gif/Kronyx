import re
import httpx


SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "ar": "Arabic", "es": "Spanish",
    "fr": "French", "de": "German", "zh-cn": "Chinese Simplified",
    "zh-tw": "Chinese Traditional", "ja": "Japanese", "ko": "Korean",
    "pt": "Portuguese", "ru": "Russian", "it": "Italian", "nl": "Dutch",
    "pl": "Polish", "tr": "Turkish", "vi": "Vietnamese", "th": "Thai",
    "id": "Indonesian", "ms": "Malay", "bn": "Bengali", "te": "Telugu",
    "ta": "Tamil", "ur": "Urdu", "mr": "Marathi", "gu": "Gujarati",
    "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi", "sv": "Swedish",
    "da": "Danish", "fi": "Finnish", "no": "Norwegian", "cs": "Czech",
    "sk": "Slovak", "ro": "Romanian", "hu": "Hungarian", "uk": "Ukrainian",
    "el": "Greek", "he": "Hebrew", "fa": "Persian", "sw": "Swahili",
    "af": "Afrikaans", "sq": "Albanian", "hy": "Armenian", "az": "Azerbaijani",
    "eu": "Basque", "be": "Belarusian", "bs": "Bosnian", "bg": "Bulgarian",
    "ca": "Catalan", "hr": "Croatian", "cy": "Welsh", "et": "Estonian",
    "tl": "Filipino", "gl": "Galician", "ka": "Georgian", "ht": "Haitian Creole",
    "is": "Icelandic", "ga": "Irish", "lv": "Latvian", "lt": "Lithuanian",
    "mk": "Macedonian", "mt": "Maltese", "sr": "Serbian", "si": "Sinhala",
    "sl": "Slovenian", "so": "Somali", "tk": "Turkmen", "uz": "Uzbek",
    "zu": "Zulu", "am": "Amharic", "my": "Burmese", "km": "Khmer",
    "lo": "Lao", "mn": "Mongolian", "ne": "Nepali", "ps": "Pashto",
    "yo": "Yoruba", "zh": "Chinese", "auto": "Auto Detect"
}

RTL_LANGUAGES = ["ar", "he", "fa", "ur", "ps"]

TONE_MODIFIERS = {
    "formal": {"style": "Use formal language, avoid contractions, be precise", "avoid": ["hey", "hi there", "sure thing", "no problem"]},
    "casual": {"style": "Be friendly and conversational", "avoid": ["Greetings", "Furthermore", "Consequently"]},
    "professional": {"style": "Be clear, direct and professional", "avoid": ["totally", "awesome", "kinda"]},
    "friendly": {"style": "Be warm, encouraging and supportive", "avoid": []},
    "technical": {"style": "Be precise, use technical terminology", "avoid": ["kinda", "sorta", "maybe"]}
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

SUPPORTED_SOURCE_TYPES = ["url", "rss", "api", "text", "faq", "product_catalog"]


def atlas_detect_language(text):
    try:
        if not text:
            return {"language": "en", "detected": False, "layer": "ATLAS"}
        try:
            from langdetect import detect
            lang = detect(text)
            return {"language": lang, "language_name": SUPPORTED_LANGUAGES.get(lang, lang), "detected": True, "is_rtl": lang in RTL_LANGUAGES, "layer": "ATLAS", "pillar": "ATLAS_PRIME"}
        except Exception:
            pass
        return {"language": "en", "language_name": "English", "detected": False, "layer": "ATLAS", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"language": "en", "detected": False, "layer": "ATLAS"}


def atlas_translate(text, target_language, api_key, db):
    try:
        if not text:
            return {"status": "error", "message": "text required", "layer": "ATLAS"}
        if len(text) > 10000:
            return {"status": "error", "message": "text too long", "layer": "ATLAS"}
        if target_language not in SUPPORTED_LANGUAGES:
            return {"status": "error", "message": f"unsupported language: {target_language}", "layer": "ATLAS"}
        if target_language == "en":
            return {"status": "success", "translated": text, "original": text, "target_language": "en", "target_language_name": "English", "is_rtl": False, "layer": "ATLAS", "pillar": "ATLAS_PRIME"}
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source="auto", target=target_language)
            translated = translator.translate(text)
            db.table("nexus_usage").insert({"api_key": api_key, "layer": "ATLAS", "action": "translate"}).execute()
            return {"status": "success", "translated": translated, "original": text, "target_language": target_language, "target_language_name": SUPPORTED_LANGUAGES.get(target_language, target_language), "is_rtl": target_language in RTL_LANGUAGES, "layer": "ATLAS", "pillar": "ATLAS_PRIME"}
        except Exception:
            pass
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ATLAS", "action": "translate"}).execute()
        return {"status": "success", "translated": text, "original": text, "target_language": target_language, "target_language_name": SUPPORTED_LANGUAGES.get(target_language, target_language), "note": "translation service not available - original returned", "layer": "ATLAS", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "translation failed", "layer": "ATLAS"}


def atlas_translate_batch(texts, target_language, api_key, db):
    try:
        if not isinstance(texts, list):
            return {"status": "error", "message": "texts must be a list", "layer": "ATLAS"}
        if len(texts) > 50:
            return {"status": "error", "message": "max 50 texts per batch", "layer": "ATLAS"}
        if target_language not in SUPPORTED_LANGUAGES:
            return {"status": "error", "message": f"unsupported language: {target_language}", "layer": "ATLAS"}
        results = []
        for i, text in enumerate(texts):
            result = atlas_translate(str(text), target_language, api_key, db)
            result["index"] = i
            results.append(result)
        success_count = sum(1 for r in results if r.get("status") == "success")
        return {"status": "complete", "results": results, "success_count": success_count, "target_language": target_language, "layer": "ATLAS", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "batch translation failed", "layer": "ATLAS"}


def atlas_auto_translate(text, user_text, api_key, db):
    try:
        detected = atlas_detect_language(user_text)
        user_lang = detected.get("language", "en")
        if user_lang == "en":
            return {"status": "no_translation_needed", "text": text, "language": "en", "layer": "ATLAS", "pillar": "ATLAS_PRIME"}
        return atlas_translate(text, user_lang, api_key, db)
    except Exception as e:
        return {"status": "error", "message": "auto translate failed", "layer": "ATLAS"}


def atlas_get_languages():
    return {"languages": SUPPORTED_LANGUAGES, "total": len(SUPPORTED_LANGUAGES), "rtl_languages": RTL_LANGUAGES, "layer": "ATLAS", "pillar": "ATLAS_PRIME"}


def genome_build_profile(business_name, business_type, tone, vocabulary, personality_traits, preferred_words, avoid_words, api_key, db):
    try:
        if not business_name:
            return {"status": "error", "message": "business_name required", "layer": "GENOME"}
        if len(business_name) > 200:
            return {"status": "error", "message": "business_name too long", "layer": "GENOME"}
        if tone not in TONE_MODIFIERS:
            tone = "professional"
        profile = {
            "business_name": business_name.replace('\x00', '').strip(),
            "business_type": (business_type or "")[:200],
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
        existing = db.table("genome_profiles").select("id").eq("api_key", api_key).execute()
        if existing.data:
            db.table("genome_profiles").update({"profile": str(profile)}).eq("api_key", api_key).execute()
        else:
            db.table("genome_profiles").insert({"api_key": api_key, "profile": str(profile)}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "GENOME", "action": "build_profile"}).execute()
        return {"status": "saved", "profile": profile, "layer": "GENOME", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "profile build failed", "layer": "GENOME"}


def genome_get_profile(api_key, db):
    try:
        result = db.table("genome_profiles").select("profile").eq("api_key", api_key).execute()
        if result.data:
            import ast
            profile = ast.literal_eval(result.data[0]["profile"])
            return {"status": "found", "profile": profile, "layer": "GENOME", "pillar": "ATLAS_PRIME"}
        return {"status": "no_profile", "message": "no personality profile set", "layer": "GENOME", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "get profile failed", "layer": "GENOME"}


def genome_inject_personality(response, api_key, db):
    try:
        if not response:
            return {"status": "error", "message": "response required", "layer": "GENOME"}
        profile_result = genome_get_profile(api_key, db)
        if profile_result.get("status") != "found":
            return {"status": "success", "response": response, "note": "no profile set - default used", "layer": "GENOME", "pillar": "ATLAS_PRIME"}
        profile = profile_result.get("profile", {})
        modified = response
        avoid_words = profile.get("avoid_words", [])
        for word in avoid_words:
            modified = modified.replace(word, "")
            modified = modified.replace(word.capitalize(), "")
        modified = re.sub(r' +', ' ', modified).strip()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "GENOME", "action": "inject_personality"}).execute()
        return {"status": "success", "original": response, "response": modified, "personality_applied": profile.get("tone", "professional"), "business_name": profile.get("business_name", ""), "layer": "GENOME", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "inject failed", "layer": "GENOME"}


def genome_generate_system_prompt(api_key, db):
    try:
        profile_result = genome_get_profile(api_key, db)
        if profile_result.get("status") != "found":
            return {"system_prompt": "You are a helpful AI assistant.", "layer": "GENOME", "pillar": "ATLAS_PRIME"}
        profile = profile_result.get("profile", {})
        traits = ", ".join(profile.get("personality_traits", ["helpful"]))
        tone = profile.get("tone", "professional")
        business = profile.get("business_name", "this business")
        style = profile.get("communication_style", "Be helpful and clear")
        avoid = profile.get("avoid_patterns", [])
        avoid_str = f"Avoid: {', '.join(avoid[:5])}" if avoid else ""
        prompt = f"You are the AI assistant for {business}.\nPersonality: {traits}.\nTone: {tone}.\nStyle: {style}.\n{avoid_str}\nAlways represent {business} professionally."
        return {"system_prompt": prompt, "profile_name": business, "layer": "GENOME", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"system_prompt": "You are a helpful AI assistant.", "layer": "GENOME"}


def nexus_connect_source(source_type, source_url, api_key, db, name="", refresh_minutes=60):
    try:
        if source_type not in SUPPORTED_SOURCE_TYPES:
            return {"status": "error", "message": f"Unsupported type. Supported: {SUPPORTED_SOURCE_TYPES}", "layer": "NEXUS"}
        if not source_url or len(source_url) > 2000:
            return {"status": "error", "message": "valid source_url required", "layer": "NEXUS"}
        config = {"url": source_url.replace('\x00', '').strip(), "name": (name or "")[:100], "refresh_minutes": min(max(refresh_minutes, 5), 1440), "source_type": source_type}
        db.table("nexus_sources").insert({"api_key": api_key, "source_type": source_type, "config": str(config), "active": True}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEXUS", "action": "connect_source"}).execute()
        return {"status": "connected", "source_type": source_type, "name": name or source_url[:50], "layer": "NEXUS", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "connect source failed", "layer": "NEXUS"}


def nexus_fetch_url(url, api_key, db):
    try:
        if not url:
            return {"status": "error", "message": "url required", "layer": "NEXUS"}
        if len(url) > 2000:
            return {"status": "error", "message": "url too long", "layer": "NEXUS"}
        if not url.startswith(("http://", "https://")):
            return {"status": "error", "message": "url must start with http or https", "layer": "NEXUS"}
        response = httpx.get(url, timeout=10, follow_redirects=True, headers={"User-Agent": "KRONYX-NEXUS/1.0"})
        if response.status_code == 200:
            db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEXUS", "action": "fetch_url"}).execute()
            return {"status": "success", "url": url, "content": response.text[:5000], "content_length": len(response.text), "layer": "NEXUS", "pillar": "ATLAS_PRIME"}
        return {"status": "error", "message": f"HTTP {response.status_code}", "layer": "NEXUS"}
    except httpx.TimeoutException:
        return {"status": "error", "message": "url request timed out", "layer": "NEXUS"}
    except Exception as e:
        return {"status": "error", "message": "fetch failed", "layer": "NEXUS"}


def nexus_add_knowledge(content, topic, api_key, db):
    try:
        if not content or not topic:
            return {"status": "error", "message": "content and topic required", "layer": "NEXUS"}
        if len(content) > 10000:
            return {"status": "error", "message": "content too long", "layer": "NEXUS"}
        entry = f"[KNOWLEDGE:{topic[:50]}] {content}"
        result = db.table("memories").insert({"content": entry, "user_id": f"nexus_{topic[:20]}", "api_key": api_key}).execute()
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEXUS", "action": "add_knowledge"}).execute()
        if result.data:
            return {"status": "stored", "topic": topic, "id": result.data[0].get("id", ""), "layer": "NEXUS", "pillar": "ATLAS_PRIME"}
        return {"status": "error", "message": "storage failed", "layer": "NEXUS"}
    except Exception as e:
        return {"status": "error", "message": "add knowledge failed", "layer": "NEXUS"}


def nexus_get_knowledge(topic, api_key, db):
    try:
        if not topic:
            return {"status": "error", "message": "topic required", "layer": "NEXUS"}
        result = db.table("memories").select("*").eq("api_key", api_key).ilike("content", f"%KNOWLEDGE:{topic}%").limit(10).execute()
        return {"status": "success", "topic": topic, "knowledge": result.data or [], "count": len(result.data or []), "layer": "NEXUS", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "get knowledge failed", "layer": "NEXUS"}


def nexus_fuse_knowledge(query, api_key, db):
    try:
        if not query:
            return {"status": "error", "message": "query required", "layer": "NEXUS"}
        all_knowledge = db.table("memories").select("content").eq("api_key", api_key).ilike("content", f"%KNOWLEDGE%").ilike("content", f"%{query[:100]}%").limit(5).execute()
        knowledge_list = all_knowledge.data or []
        fused = " | ".join([k.get("content", "")[:200] for k in knowledge_list if k.get("content")])
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "NEXUS", "action": "fuse_knowledge"}).execute()
        return {"status": "success", "query": query, "fused_knowledge": fused[:3000] if fused else "no knowledge found for this query", "sources_used": len(knowledge_list), "layer": "NEXUS", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "fuse knowledge failed", "layer": "NEXUS"}


def nexus_get_sources(api_key, db):
    try:
        result = db.table("nexus_sources").select("*").eq("api_key", api_key).eq("active", True).execute()
        return {"sources": result.data or [], "total": len(result.data or []), "layer": "NEXUS", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"sources": [], "total": 0, "layer": "NEXUS"}


def babel_translate_domain(concept, source_domain, target_domain, api_key, db):
    try:
        if not concept or not source_domain or not target_domain:
            return {"status": "error", "message": "concept, source_domain and target_domain required", "layer": "BABEL"}
        if len(concept) > 10000:
            return {"status": "error", "message": "concept too long", "layer": "BABEL"}
        if source_domain not in COGNITIVE_GRAMMARS:
            return {"status": "error", "message": f"unknown source domain. Available: {list(COGNITIVE_GRAMMARS.keys())}", "layer": "BABEL"}
        if target_domain not in COGNITIVE_GRAMMARS:
            return {"status": "error", "message": f"unknown target domain. Available: {list(COGNITIVE_GRAMMARS.keys())}", "layer": "BABEL"}
        concept_clean = concept.replace('\x00', '').strip()
        source = COGNITIVE_GRAMMARS[source_domain]
        target = COGNITIVE_GRAMMARS[target_domain]
        translation = f"'{concept_clean[:100]}' in {source['thinking_style'][:60]} translates to {target['thinking_style'][:60]}. Key question: {target['translation_lens']}. This brings {target['strength']} to bear on the problem."
        novel_insight = f"The unexpected insight from translating '{concept_clean[:50]}' from {source_domain} to {target_domain}: patterns that appear fixed in one domain become dynamic and malleable in the other, revealing hidden solution spaces."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "BABEL", "action": "translate_domain"}).execute()
        return {"status": "success", "concept": concept_clean[:200], "source_domain": source_domain, "target_domain": target_domain, "translation": translation, "novel_insight": novel_insight, "source_lens": source["translation_lens"], "target_lens": target["translation_lens"], "layer": "BABEL", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "domain translation failed", "layer": "BABEL"}


def babel_get_domains():
    return {"domains": {k: {"thinking_style": v["thinking_style"], "strength": v["strength"]} for k, v in COGNITIVE_GRAMMARS.items()}, "total": len(COGNITIVE_GRAMMARS), "layer": "BABEL", "pillar": "ATLAS_PRIME"}


def babel_apply_lens(problem, domain, api_key, db):
    try:
        if not problem or not domain:
            return {"status": "error", "message": "problem and domain required", "layer": "BABEL"}
        if domain not in COGNITIVE_GRAMMARS:
            return {"status": "error", "message": f"unknown domain. Available: {list(COGNITIVE_GRAMMARS.keys())}", "layer": "BABEL"}
        grammar = COGNITIVE_GRAMMARS[domain]
        analysis = f"Viewing '{problem[:100]}' through {domain} lens: {grammar['translation_lens']} This reveals {grammar['strength']} as the key to understanding."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "BABEL", "action": "apply_lens"}).execute()
        return {"status": "success", "problem": problem[:200], "domain": domain, "analysis": analysis, "thinking_style": grammar["thinking_style"], "strength": grammar["strength"], "layer": "BABEL", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "lens application failed", "layer": "BABEL"}


def eternal_analyze_impact(decision, domain, api_key, db, time_horizon_years=100):
    try:
        if not decision:
            return {"status": "error", "message": "decision required", "layer": "ETERNAL"}
        if len(decision) > 10000:
            return {"status": "error", "message": "decision too long", "layer": "ETERNAL"}
        time_horizon_years = min(max(time_horizon_years, 10), 1000)
        decision_clean = decision.replace('\x00', '').strip()
        d_lower = decision_clean.lower()
        matching = []
        for name, data in CIVILIZATIONAL_PATTERNS.items():
            if any(w in d_lower for w in name.split("_")):
                matching.append({"pattern": name, "description": data["pattern"], "timescale": data["timescale"], "historical_parallel": data["historical_examples"][0]})
        generational_impact = {10: {"scope": "1_generation", "description": "Affects current workforce and children"}, 30: {"scope": "2_generations", "description": "Affects grandchildren and institutions"}, 100: {"scope": "5_generations", "description": "Affects fundamental social structures"}, 300: {"scope": "10_generations", "description": "Affects language culture and values"}, 1000: {"scope": "civilization", "description": "Affects what kind of civilization humans become"}}
        gen_impact = {"scope": "civilization", "description": "Affects what kind of civilization humans become"}
        for threshold, impact in sorted(generational_impact.items()):
            if time_horizon_years <= threshold:
                gen_impact = impact
                break
        trajectory = f"Over {time_horizon_years} years following {matching[0]['pattern']} pattern. Historical parallel: {matching[0]['historical_parallel']}." if matching else f"Over {time_horizon_years} years decisions of this type reshape institutional and cultural landscape significantly."
        recommendation = "Build reversibility into implementation. Plan for plateau phase after explosive growth." if matching else "Consider generational consequences. Prioritize reversibility over optimization."
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ETERNAL", "action": "analyze_impact"}).execute()
        return {"status": "success", "decision": decision_clean[:200], "time_horizon_years": time_horizon_years, "matching_civilizational_patterns": matching[:3], "generational_impact": gen_impact, "civilizational_trajectory": trajectory, "long_term_recommendation": recommendation, "layer": "ETERNAL", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "impact analysis failed", "layer": "ETERNAL"}


def eternal_get_patterns():
    return {"patterns": {k: {"pattern": v["pattern"], "timescale": v["timescale"]} for k, v in CIVILIZATIONAL_PATTERNS.items()}, "total": len(CIVILIZATIONAL_PATTERNS), "layer": "ETERNAL", "pillar": "ATLAS_PRIME"}


def eternal_compare_historical(current_situation, api_key, db):
    try:
        if not current_situation:
            return {"status": "error", "message": "current_situation required", "layer": "ETERNAL"}
        s_lower = current_situation.lower()
        parallels = []
        for name, data in CIVILIZATIONAL_PATTERNS.items():
            for example in data["historical_examples"]:
                if any(word in s_lower for word in example.split()):
                    parallels.append({"historical_event": example, "pattern": data["pattern"], "timescale": data["timescale"], "relevance": "The current situation mirrors this historical pattern"})
        if not parallels:
            parallels = [{"historical_event": "Industrial Revolution", "pattern": "Technology adoption S-curve followed by societal restructuring", "timescale": "50-100 years", "relevance": "Most transformative situations follow this general pattern"}]
        db.table("nexus_usage").insert({"api_key": api_key, "layer": "ETERNAL", "action": "compare_historical"}).execute()
        return {"status": "success", "current_situation": current_situation[:200], "historical_parallels": parallels[:5], "layer": "ETERNAL", "pillar": "ATLAS_PRIME"}
    except Exception as e:
        return {"status": "error", "message": "historical comparison failed", "layer": "ETERNAL"}
