import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "kronyx-change-this-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = "KRONYX <noreply@kronyx.app>"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
APP_NAME = "KRONYX"
APP_VERSION = "3.0.0"
APP_URL = os.getenv("APP_URL", "https://kronyx.vercel.app")
ADMIN_KEY = os.getenv("ADMIN_KEY", "")
API_KEY_PREFIX = "kr_live_"
DAILY_API_LIMIT = 10000
MAX_LOGIN_ATTEMPTS = 5
LOGIN_BLOCK_MINUTES = 30
MAX_REQUEST_SIZE_BYTES = 1000000
MAX_INPUT_LENGTH = 10000
REQUEST_TIMEOUT_SECONDS = 30
MEMORY_AUTO_DELETE_DAYS = 90
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_EMAIL_LENGTH = 254
IP_RATE_LIMIT_PER_MINUTE = 500

ALL_PILLARS = [
    "NEXUS_CORE",
    "AEGIS_SHIELD",
    "PROMETHEUS_MIND",
    "ATLAS_PRIME",
    "SINGULARITY_ENGINE"
]

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

ALL_LAYERS = [
    "memex", "flux", "pulse", "insight", "echo",
    "vault", "sentinel", "abyss", "infinite", "truthfield",
    "oracle", "lens", "deep", "genesis_prime",
    "atlas", "genome", "nexus", "babel", "eternal",
    "akasha", "zero", "apex", "fractal", "origin"
]

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
