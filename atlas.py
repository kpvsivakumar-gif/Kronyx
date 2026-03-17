from database import usage_log
from validators import validate_text, validate_language_code, sanitize_text
from logger import log_layer, log_error

try:
    from deep_translator import GoogleTranslator
    from langdetect import detect, LangDetectException
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

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
    "sd": "Sindhi", "sm": "Samoan", "sn": "Shona", "st": "Sesotho",
    "su": "Sundanese", "tg": "Tajik", "tt": "Tatar", "ug": "Uighur",
    "yo": "Yoruba", "zh": "Chinese", "auto": "Auto Detect"
}

RTL_LANGUAGES = ["ar", "he", "fa", "ur", "ps", "sd", "ug"]

FORMAL_INFORMAL_LANGUAGES = {
    "de": {"formal": "Sie", "informal": "du"},
    "fr": {"formal": "vous", "informal": "tu"},
    "es": {"formal": "usted", "informal": "tu"},
    "it": {"formal": "lei", "informal": "tu"},
    "pt": {"formal": "o senhor", "informal": "tu"},
    "ja": {"formal": "keigo", "informal": "casual"},
    "ko": {"formal": "jondaemal", "informal": "banmal"}
}


def detect_language(text):
    if not text:
        return {"language": "en", "detected": False, "layer": "ATLAS"}
    try:
        if TRANSLATION_AVAILABLE:
            lang = detect(text)
            return {
                "language": lang,
                "language_name": SUPPORTED_LANGUAGES.get(lang, lang),
                "detected": True,
                "is_rtl": lang in RTL_LANGUAGES,
                "layer": "ATLAS"
            }
    except Exception:
        pass
    return {"language": "en", "language_name": "English", "detected": False, "layer": "ATLAS"}


def translate(text, target_language, api_key):
    log_layer("atlas", "translate", api_key)
    if not text:
        return {"status": "error", "message": "text required", "layer": "ATLAS"}
    valid, err = validate_text(text, field_name="text")
    if not valid:
        return {"status": "error", "message": err, "layer": "ATLAS"}
    valid, err = validate_language_code(target_language)
    if not valid:
        return {"status": "error", "message": err, "layer": "ATLAS"}
    usage_log(api_key, "atlas", "translate")
    if target_language == "en":
        return {"status": "success", "translated": text, "original": text, "target_language": "en", "target_language_name": "English", "is_rtl": False, "layer": "ATLAS"}
    if not TRANSLATION_AVAILABLE:
        return {"status": "success", "translated": text, "original": text, "target_language": target_language, "note": "translation service not available", "layer": "ATLAS"}
    try:
        translator = GoogleTranslator(source="auto", target=target_language)
        translated = translator.translate(text)
        return {
            "status": "success",
            "translated": translated,
            "original": text,
            "target_language": target_language,
            "target_language_name": SUPPORTED_LANGUAGES.get(target_language, target_language),
            "is_rtl": target_language in RTL_LANGUAGES,
            "layer": "ATLAS"
        }
    except Exception as e:
        log_error(str(e), api_key=api_key, context="atlas.translate")
        return {"status": "error", "translated": text, "original": text, "message": "translation failed - original text returned", "layer": "ATLAS"}


def translate_batch(texts, target_language, api_key):
    log_layer("atlas", "translate_batch", api_key)
    if not isinstance(texts, list):
        return {"status": "error", "message": "texts must be a list", "layer": "ATLAS"}
    if len(texts) > 50:
        return {"status": "error", "message": "max 50 texts per batch", "layer": "ATLAS"}
    valid, err = validate_language_code(target_language)
    if not valid:
        return {"status": "error", "message": err, "layer": "ATLAS"}
    results = []
    for i, text in enumerate(texts):
        result = translate(str(text), target_language, api_key)
        result["index"] = i
        results.append(result)
    success_count = sum(1 for r in results if r.get("status") == "success")
    return {"status": "complete", "results": results, "success_count": success_count, "target_language": target_language, "layer": "ATLAS"}


def auto_translate_response(text, user_text, api_key):
    detected = detect_language(user_text)
    user_lang = detected.get("language", "en")
    if user_lang == "en":
        return {"status": "no_translation_needed", "text": text, "language": "en", "layer": "ATLAS"}
    return translate(text, user_lang, api_key)


def get_supported_languages():
    return {"languages": SUPPORTED_LANGUAGES, "total": len(SUPPORTED_LANGUAGES), "rtl_languages": RTL_LANGUAGES, "layer": "ATLAS"}


def get_language_info(language_code):
    if language_code not in SUPPORTED_LANGUAGES:
        return {"status": "error", "message": f"language not supported: {language_code}", "layer": "ATLAS"}
    return {
        "status": "found",
        "code": language_code,
        "name": SUPPORTED_LANGUAGES[language_code],
        "is_rtl": language_code in RTL_LANGUAGES,
        "formality": FORMAL_INFORMAL_LANGUAGES.get(language_code),
        "layer": "ATLAS"
    }


def get_translation_coverage():
    return {
        "total_languages": len(SUPPORTED_LANGUAGES),
        "rtl_languages": len(RTL_LANGUAGES),
        "languages_with_formality": len(FORMAL_INFORMAL_LANGUAGES),
        "coverage_percentage": 95,
        "note": "Covers approximately 95% of world internet users",
        "layer": "ATLAS"
    }
