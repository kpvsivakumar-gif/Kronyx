import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from config import (
    APP_NAME, APP_VERSION, APP_DESCRIPTION,
    ALL_PILLARS, ALL_SYSTEMS, ALL_LAYERS, ALL_ELITE,
    TOTAL_CAPABILITIES, PILLAR_DESCRIPTIONS, SYSTEM_DESCRIPTIONS,
    ELITE_DESCRIPTIONS, ENVIRONMENT
)
from logger import log_startup, log_shutdown, log_error
from database import get_db, is_db_connected
from middleware import (
    SecurityHeadersMiddleware, RequestSizeLimitMiddleware,
    IPRateLimitMiddleware, RequestLoggingMiddleware, TimeoutMiddleware
)
from api import router
from pillar_nexus import pulse_health_check

# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(
    title=f"{APP_NAME} API",
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "KRONYX Support",
        "url": "https://kronyx.app",
        "email": "support@kronyx.app"
    },
    license_info={
        "name": "KRONYX Commercial License",
        "url": "https://kronyx.app/terms"
    }
)

# ============================================================
# MIDDLEWARE STACK
# ============================================================

app.add_middleware(TimeoutMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(IPRateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time", "X-Request-ID"]
)

# ============================================================
# INCLUDE ROUTERS
# ============================================================

app.include_router(router)

# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error(str(exc), context=f"unhandled_exception {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again.",
            "support": "support@kronyx.app"
        }
    )

# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/", tags=["System"])
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "tagline": "The AWS of AI Infrastructure",
        "description": APP_DESCRIPTION,
        "status": "operational",
        "environment": ENVIRONMENT,
        "pillars": ALL_PILLARS,
        "total_pillars": len(ALL_PILLARS),
        "pillar_descriptions": PILLAR_DESCRIPTIONS,
        "systems": ALL_SYSTEMS,
        "total_systems": len(ALL_SYSTEMS),
        "system_descriptions": SYSTEM_DESCRIPTIONS,
        "total_layers": len(ALL_LAYERS),
        "layers": ALL_LAYERS,
        "elite_features": ALL_ELITE,
        "total_elite_features": len(ALL_ELITE),
        "elite_descriptions": ELITE_DESCRIPTIONS,
        "total_capabilities": TOTAL_CAPABILITIES,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "status_page": "/status"
    }


@app.get("/health", tags=["System"])
async def health():
    db = get_db()
    if not db:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "message": "Database connection failed"
            }
        )
    result = pulse_health_check(db)
    status_code = 200 if result.get("status") == "healthy" else 503
    return JSONResponse(status_code=status_code, content=result)


@app.get("/status", tags=["System"])
async def status():
    db_connected = is_db_connected()
    return {
        "status": "operational" if db_connected else "degraded",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "database": "connected" if db_connected else "disconnected",
        "total_capabilities": TOTAL_CAPABILITIES,
        "pillars_active": len(ALL_PILLARS),
        "systems_active": len(ALL_SYSTEMS),
        "layers_active": len(ALL_LAYERS),
        "elite_features_active": len(ALL_ELITE)
    }


@app.get("/capabilities", tags=["System"])
async def capabilities():
    return {
        "total_capabilities": TOTAL_CAPABILITIES,
        "pillars": {p: PILLAR_DESCRIPTIONS[p] for p in ALL_PILLARS},
        "systems": {s: SYSTEM_DESCRIPTIONS[s] for s in ALL_SYSTEMS},
        "layers": ALL_LAYERS,
        "elite_features": {e: ELITE_DESCRIPTIONS[e] for e in ALL_ELITE}
    }


# ============================================================
# LIFECYCLE EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    log_startup()


@app.on_event("shutdown")
async def shutdown_event():
    log_shutdown()


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WEB_CONCURRENCY", 1))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info" if ENVIRONMENT == "production" else "debug",
        access_log=False
    )
