import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "kronyx-change-this-secret-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = "KRONYX <noreply@kronyx.app>"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
APP_NAME = "KRONYX"
APP_VERSION = "1.0.0"
APP_URL = os.getenv("APP_URL", "https://kronyx.vercel.app")
ADMIN_KEY = os.getenv("ADMIN_KEY", "")
API_KEY_PREFIX = "kr_live_"
MAX_API_KEYS_PER_USER = 2
DAILY_API_LIMIT = 10000
MAX_LOGIN_ATTEMPTS = 5
LOGIN_BLOCK_MINUTES = 30
MAX_REQUEST_SIZE_BYTES = 1000000
MAX_INPUT_LENGTH = 10000
REQUEST_TIMEOUT_SECONDS = 30
MEMORY_AUTO_DELETE_DAYS = 90
MAX_MEMORIES_PER_RECALL = 20
MAX_MEMORY_CONTENT_LENGTH = 5000
CACHE_MAX_RESPONSE_LENGTH = 50000
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_EMAIL_LENGTH = 254
IP_RATE_LIMIT_PER_MINUTE = 500

ALL_LAYERS = [
    "memex", "sentinel", "flux", "vault", "atlas",
    "pulse", "insight", "oracle", "genome", "nexus",
    "echo", "lens", "prima", "duality", "akasha",
    "zero", "deep", "apex", "babel", "eternal",
    "infinite", "abyss", "fractal", "origin", "genesis_prime"
]
