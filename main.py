import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from api import router
from middleware import SecurityHeadersMiddleware, RequestSizeLimitMiddleware, IPRateLimitMiddleware, RequestLoggingMiddleware, TimeoutMiddleware
from config import APP_NAME, APP_VERSION, ALL_LAYERS
from logger import log_startup


app = FastAPI(title=f"{APP_NAME} API", description="Universal AI Infrastructure Platform - 25 Layers", version=APP_VERSION, docs_url="/docs", redoc_url="/redoc")

app.add_middleware(TimeoutMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(IPRateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(router)


@app.get("/")
async def root():
    return {"name": APP_NAME, "version": APP_VERSION, "status": "operational", "layers": ALL_LAYERS, "total_layers": len(ALL_LAYERS), "docs": "/docs"}


@app.get("/health")
async def health():
    from pulse import health_check
    return health_check()


@app.get("/status")
async def status():
    return {"status": "operational", "version": APP_VERSION, "layers_active": len(ALL_LAYERS)}


@app.on_event("startup")
async def startup_event():
    log_startup()
    try:
        from background_tasks import start_background_tasks
        start_background_tasks()
    except Exception:
        pass


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from background_tasks import stop_background_tasks
        stop_background_tasks()
    except Exception:
        pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
