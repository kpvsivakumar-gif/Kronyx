import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# APPLICATION IDENTITY
# ============================================================
APP_NAME = "KRONYX"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = "The AWS of AI Infrastructure - 54 Capabilities - God Level Intelligence"
APP_AUTHOR = "KRONYX Inc."
APP_URL = os.getenv("APP_URL", "https://kronyx.app")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT != "production"

# ============================================================
# DATABASE
# ============================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ============================================================
# AUTHENTICATION AND SECURITY
# ============================================================
SECRET_KEY = os.getenv("SECRET_KEY", "kronyx-change-this-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
REFRESH_TOKEN_EXPIRE_DAYS = 30
API_KEY_PREFIX = "kr_live_"
API_KEY_LENGTH = 32

# ============================================================
# EMAIL
# ============================================================
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = "KRONYX <noreply@kronyx.app>"
FROM_NAME = "KRONYX"
SUPPORT_EMAIL = "support@kronyx.app"

# ============================================================
# ADMIN
# ============================================================
ADMIN_KEY = os.getenv("ADMIN_KEY", "")

# ============================================================
# RATE LIMITING
# ============================================================
DAILY_API_LIMIT_FREE = 10000
DAILY_API_LIMIT_PRO = 100000
DAILY_API_LIMIT_ENTERPRISE = 1000000
DAILY_API_LIMIT = DAILY_API_LIMIT_FREE
IP_RATE_LIMIT_PER_MINUTE = 500
IP_RATE_LIMIT_PER_HOUR = 10000
BURST_LIMIT = 50

# ============================================================
# SECURITY LIMITS
# ============================================================
MAX_LOGIN_ATTEMPTS = 5
LOGIN_BLOCK_MINUTES = 30
MAX_REQUEST_SIZE_BYTES = 2000000
MAX_INPUT_LENGTH = 10000
MAX_CONTENT_LENGTH = 50000
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_EMAIL_LENGTH = 254
MAX_USER_ID_LENGTH = 256
MAX_AI_ID_LENGTH = 100
REQUEST_TIMEOUT_SECONDS = 30

# ============================================================
# MEMORY SETTINGS
# ============================================================
MEMORY_AUTO_DELETE_DAYS = 90
MAX_MEMORIES_PER_USER = 10000
MAX_MEMORY_CONTENT_LENGTH = 5000
MAX_BULK_MEMORIES = 50
MAX_BULK_CACHE_ITEMS = 100
MAX_RECALL_LIMIT = 20
MAX_TAG_SEARCH_LIMIT = 20

# ============================================================
# CACHE SETTINGS
# ============================================================
CACHE_MAX_RESPONSE_SIZE = 50000
CACHE_DEFAULT_TTL_HOURS = 24
CACHE_MAX_QUESTION_LENGTH = 10000

# ============================================================
# SECURITY HEADERS
# ============================================================
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
    "X-Powered-By": "KRONYX",
}

# ============================================================
# 5 ELITE PILLARS
# ============================================================
ALL_PILLARS = [
    "NEXUS_CORE",
    "AEGIS_SHIELD",
    "PROMETHEUS_MIND",
    "ATLAS_PRIME",
    "SINGULARITY_ENGINE"
]

PILLAR_DESCRIPTIONS = {
    "NEXUS_CORE": "AI Memory Speed Health Analytics Verification",
    "AEGIS_SHIELD": "Security Protection Ethics Compliance Infinite Reasoning",
    "PROMETHEUS_MIND": "Intent Detection Context Understanding Deep Meaning Genesis",
    "ATLAS_PRIME": "Translation Personality Knowledge Domain Cognitive Temporal",
    "SINGULARITY_ENGINE": "Quantum Superposition Universal Patterns Zero Emergence Fractal Origin"
}

# ============================================================
# 14 GOD SYSTEMS
# ============================================================
ALL_SYSTEMS = [
    "KRONYX_PROTOCOL",
    "KRONYX_IDENTITY",
    "KRONYX_TRANSPARENCY",
    "KRONYX_LIVE_LEARNING",
    "KRONYX_RELATIONSHIP",
    "KRONYX_VALUE",
    "KRONYX_NEURAL_BUS",
    "KRONYX_OBSERVATORY",
    "KRONYX_TIME_MACHINE",
    "KRONYX_CONSCIENCE",
    "KRONYX_ANIMA",
    "KRONYX_AKASHIC",
    "KRONYX_OMEGA",
    "KRONYX_EMPATHON"
]

SYSTEM_DESCRIPTIONS = {
    "KRONYX_PROTOCOL": "AI to AI communication standard",
    "KRONYX_IDENTITY": "AI reputation and trust scoring",
    "KRONYX_TRANSPARENCY": "Decision audit trail and compliance",
    "KRONYX_LIVE_LEARNING": "Real-time behavioral correction",
    "KRONYX_RELATIONSHIP": "User-AI relationship depth tracking",
    "KRONYX_VALUE": "Interaction value and ROI measurement",
    "KRONYX_NEURAL_BUS": "Real-time AI event messaging",
    "KRONYX_OBSERVATORY": "AI metrics and anomaly detection",
    "KRONYX_TIME_MACHINE": "AI state snapshots and rollback",
    "KRONYX_CONSCIENCE": "Ethical decision checking",
    "KRONYX_ANIMA": "AI soul and continuous identity",
    "KRONYX_AKASHIC": "Collective human wisdom substrate",
    "KRONYX_OMEGA": "User trajectory prediction engine",
    "KRONYX_EMPATHON": "Functional emotional reality engine"
}

# ============================================================
# 24 CORE LAYERS
# ============================================================
ALL_LAYERS = [
    "memex", "flux", "pulse", "insight", "echo",
    "vault", "sentinel", "abyss", "infinite", "truthfield",
    "oracle", "lens", "prima", "deep", "genesis_prime",
    "atlas", "genome", "nexus", "babel", "eternal",
    "akasha", "zero", "apex", "fractal", "origin"
]

LAYER_PILLARS = {
    "memex": "NEXUS_CORE",
    "flux": "NEXUS_CORE",
    "pulse": "NEXUS_CORE",
    "insight": "NEXUS_CORE",
    "echo": "NEXUS_CORE",
    "vault": "AEGIS_SHIELD",
    "sentinel": "AEGIS_SHIELD",
    "abyss": "AEGIS_SHIELD",
    "infinite": "AEGIS_SHIELD",
    "truthfield": "AEGIS_SHIELD",
    "oracle": "PROMETHEUS_MIND",
    "lens": "PROMETHEUS_MIND",
    "prima": "PROMETHEUS_MIND",
    "deep": "PROMETHEUS_MIND",
    "genesis_prime": "PROMETHEUS_MIND",
    "atlas": "ATLAS_PRIME",
    "genome": "ATLAS_PRIME",
    "nexus": "ATLAS_PRIME",
    "babel": "ATLAS_PRIME",
    "eternal": "ATLAS_PRIME",
    "akasha": "SINGULARITY_ENGINE",
    "zero": "SINGULARITY_ENGINE",
    "apex": "SINGULARITY_ENGINE",
    "fractal": "SINGULARITY_ENGINE",
    "origin": "SINGULARITY_ENGINE"
}

# ============================================================
# 11 ELITE FEATURES
# ============================================================
ALL_ELITE = [
    "NEURALFORGE",
    "QUANTUMROUTE",
    "TEMPORALMIND",
    "EIGENCORE",
    "SHADOWTEST",
    "COGNITIVEMAP",
    "SYNTHSTREAM",
    "DRIFTGUARD",
    "INFINITESCALE",
    "CAUSALITY",
    "CONTEXTFORGE"
]

ELITE_DESCRIPTIONS = {
    "NEURALFORGE": "World's first AI behavior compiler - cross model portable",
    "QUANTUMROUTE": "Intelligent request routing to optimal model - 80% cost savings",
    "TEMPORALMIND": "Temporal knowledge intelligence - knows what ages and what doesnt",
    "EIGENCORE": "Mathematical identity distillation from institutional knowledge",
    "SHADOWTEST": "Shadow deployment testing with zero user impact",
    "COGNITIVEMAP": "AI knowledge graph - maps what AI knows and does not know",
    "SYNTHSTREAM": "Multi-model response synthesis - better than any single model",
    "DRIFTGUARD": "Behavioral drift detection before users notice",
    "INFINITESCALE": "Elastic intelligence - infinite capacity zero waste",
    "CAUSALITY": "Causal reasoning infrastructure - why not just what",
    "CONTEXTFORGE": "Infinite context window for any AI model"
}

# ============================================================
# TOTALS
# ============================================================
TOTAL_PILLARS = len(ALL_PILLARS)
TOTAL_SYSTEMS = len(ALL_SYSTEMS)
TOTAL_LAYERS = len(ALL_LAYERS)
TOTAL_ELITE = len(ALL_ELITE)
TOTAL_CAPABILITIES = TOTAL_PILLARS + TOTAL_SYSTEMS + TOTAL_LAYERS + TOTAL_ELITE

# ============================================================
# SUPPORTED LANGUAGES FOR ATLAS
# ============================================================
SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "ar": "Arabic", "es": "Spanish",
    "fr": "French", "de": "German", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "pt": "Portuguese", "ru": "Russian", "it": "Italian",
    "nl": "Dutch", "pl": "Polish", "tr": "Turkish", "vi": "Vietnamese",
    "th": "Thai", "id": "Indonesian", "ms": "Malay", "bn": "Bengali",
    "te": "Telugu", "ta": "Tamil", "ur": "Urdu", "mr": "Marathi",
    "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi",
    "sv": "Swedish", "da": "Danish", "fi": "Finnish", "no": "Norwegian",
    "cs": "Czech", "sk": "Slovak", "ro": "Romanian", "hu": "Hungarian",
    "uk": "Ukrainian", "el": "Greek", "he": "Hebrew", "fa": "Persian",
    "sw": "Swahili", "af": "Afrikaans", "sq": "Albanian", "hy": "Armenian",
    "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian", "bs": "Bosnian",
    "bg": "Bulgarian", "ca": "Catalan", "hr": "Croatian", "cy": "Welsh",
    "et": "Estonian", "tl": "Filipino", "gl": "Galician", "ka": "Georgian",
    "ht": "Haitian Creole", "is": "Icelandic", "ga": "Irish", "lv": "Latvian",
    "lt": "Lithuanian", "mk": "Macedonian", "mt": "Maltese", "sr": "Serbian",
    "si": "Sinhala", "sl": "Slovenian", "so": "Somali", "tk": "Turkmen",
    "uz": "Uzbek", "zu": "Zulu", "am": "Amharic", "my": "Burmese",
    "km": "Khmer", "lo": "Lao", "mn": "Mongolian", "ne": "Nepali",
    "ps": "Pashto", "yo": "Yoruba", "auto": "Auto Detect"
}

RTL_LANGUAGES = ["ar", "he", "fa", "ur", "ps"]

# ============================================================
# AI MODEL REGISTRY FOR QUANTUMROUTE
# ============================================================
AI_MODELS = {
    "claude": {
        "provider": "Anthropic",
        "strengths": ["nuanced_reasoning", "safety", "long_context", "instruction_following", "ethics"],
        "cost_tier": "high",
        "speed_tier": "medium",
        "best_for": ["complex_reasoning", "writing", "analysis", "sensitive_topics", "long_documents"],
        "context_window": 200000
    },
    "gpt4": {
        "provider": "OpenAI",
        "strengths": ["reasoning", "code", "math", "broad_knowledge", "function_calling"],
        "cost_tier": "high",
        "speed_tier": "medium",
        "best_for": ["coding", "math", "broad_questions", "structured_output"],
        "context_window": 128000
    },
    "gemini": {
        "provider": "Google",
        "strengths": ["factual_recall", "multimodal", "search_grounded", "speed"],
        "cost_tier": "medium",
        "speed_tier": "fast",
        "best_for": ["factual_questions", "current_events", "multimodal", "search"],
        "context_window": 1000000
    },
    "llama": {
        "provider": "Meta",
        "strengths": ["code", "efficiency", "open_source", "customizable"],
        "cost_tier": "low",
        "speed_tier": "fast",
        "best_for": ["simple_tasks", "code_completion", "classification", "batch"],
        "context_window": 32000
    },
    "mistral": {
        "provider": "Mistral AI",
        "strengths": ["efficiency", "multilingual", "fast", "european"],
        "cost_tier": "low",
        "speed_tier": "very_fast",
        "best_for": ["translation", "simple_qa", "classification", "european_languages"],
        "context_window": 32000
    }
}

# ============================================================
# TEMPORAL DECAY RATES FOR TEMPORALMIND
# ============================================================
TEMPORAL_DECAY_RATES = {
    "stock_prices": {"decay_hours": 0.1, "category": "financial", "description": "Changes every second"},
    "crypto_prices": {"decay_hours": 0.05, "category": "financial", "description": "Changes every few minutes"},
    "news_events": {"decay_hours": 24, "category": "news", "description": "Changes daily"},
    "sports_scores": {"decay_hours": 0.5, "category": "sports", "description": "Changes during games"},
    "weather": {"decay_hours": 6, "category": "environmental", "description": "Changes every few hours"},
    "product_prices": {"decay_hours": 168, "category": "commercial", "description": "Changes weekly"},
    "laws_regulations": {"decay_hours": 8760, "category": "legal", "description": "Changes annually"},
    "scientific_facts": {"decay_hours": 87600, "category": "science", "description": "Changes over decades"},
    "historical_facts": {"decay_hours": 0, "category": "history", "description": "Does not change"},
    "medical_guidelines": {"decay_hours": 2160, "category": "medical", "description": "Changes quarterly"},
    "technology_specs": {"decay_hours": 720, "category": "technology", "description": "Changes monthly"},
    "company_information": {"decay_hours": 720, "category": "business", "description": "Changes monthly"},
    "drug_interactions": {"decay_hours": 4380, "category": "medical", "description": "Changes semi-annually"},
    "exchange_rates": {"decay_hours": 1, "category": "financial", "description": "Changes hourly"},
    "software_versions": {"decay_hours": 168, "category": "technology", "description": "Changes weekly"},
    "political_events": {"decay_hours": 24, "category": "politics", "description": "Changes daily"},
    "population_data": {"decay_hours": 8760, "category": "demographics", "description": "Changes annually"},
    "research_papers": {"decay_hours": 43800, "category": "academic", "description": "Changes every 5 years"},
    "cultural_trends": {"decay_hours": 720, "category": "culture", "description": "Changes monthly"}
}

# ============================================================
# QUERY COMPLEXITY SIGNALS FOR QUANTUMROUTE
# ============================================================
QUERY_COMPLEXITY = {
    "simple": ["what is", "define", "who is", "when was", "where is", "yes or no", "list", "name", "give me", "how many"],
    "moderate": ["explain", "describe", "how does", "compare", "summarize", "what are the", "tell me about"],
    "complex": ["analyze", "evaluate", "synthesize", "design", "create", "develop", "critique", "argue", "assess"],
    "expert": ["derive", "prove", "optimize", "implement", "architect", "research", "theorize", "mathematically"]
}

# ============================================================
# TASK TYPE SIGNALS FOR QUANTUMROUTE
# ============================================================
QUERY_TASK_TYPES = {
    "coding": ["code", "function", "debug", "programming", "python", "javascript", "sql", "implement", "script", "algorithm", "bug", "error", "compile"],
    "math": ["calculate", "equation", "formula", "solve", "derivative", "integral", "proof", "algebra", "calculus", "statistics", "probability"],
    "creative": ["write", "poem", "story", "creative", "imagine", "fiction", "narrative", "essay", "blog", "content", "generate"],
    "factual": ["what is", "who is", "when was", "where is", "fact", "history", "define", "meaning", "origin"],
    "analysis": ["analyze", "evaluate", "compare", "assess", "critique", "review", "examine", "investigate"],
    "translation": ["translate", "in french", "in spanish", "in hindi", "language", "in german", "in arabic"],
    "sensitive": ["medical", "legal", "financial", "mental health", "suicide", "harm", "therapy", "diagnosis", "treatment"],
    "reasoning": ["why", "reason", "because", "cause", "explain", "logic", "argument", "therefore", "conclude"],
    "summarization": ["summarize", "brief", "overview", "summary", "tldr", "short version", "key points"],
    "classification": ["classify", "categorize", "sort", "label", "identify", "determine", "detect", "is this"]
}
