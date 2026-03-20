import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from api import router
from middleware import SecurityHeadersMiddleware, RequestSizeLimitMiddleware, IPRateLimitMiddleware, RequestLoggingMiddleware, TimeoutMiddleware
from config import APP_NAME, APP_VERSION, ALL_PILLARS, ALL_SYSTEMS, ALL_LAYERS
from logger import log_startup
from database import get_db
from pillar_nexus import pulse_health_check

app = FastAPI(
    title=f"{APP_NAME} API",
    description="The AWS of AI Infrastructure - 5 Elite Pillars - 18 Systems - God Level Intelligence",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(TimeoutMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(IPRateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "tagline": "The AWS of AI Infrastructure",
        "status": "operational",
        "pillars": ALL_PILLARS,
        "total_pillars": len(ALL_PILLARS),
        "systems": ALL_SYSTEMS,
        "total_systems": len(ALL_SYSTEMS),
        "total_layers": len(ALL_LAYERS),
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    db = get_db()
    if not db:
        return {"status": "unhealthy", "database": "disconnected"}
    return pulse_health_check(db)


@app.get("/status")
async def status():
    return {
        "status": "operational",
        "version": APP_VERSION,
        "pillars_active": len(ALL_PILLARS),
        "systems_active": len(ALL_SYSTEMS),
        "layers_active": len(ALL_LAYERS)
    }


@app.on_event("startup")
async def startup_event():
    log_startup()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
