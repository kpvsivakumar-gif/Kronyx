import time
import asyncio
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import MAX_REQUEST_SIZE_BYTES, REQUEST_TIMEOUT_SECONDS
from security import record_ip_request, SECURITY_HEADERS
from logger import log_request, log_security, log_warning


# ============================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers[key] = value
        response.headers["X-Request-ID"] = request.headers.get("x-request-id", "")
        return response


# ============================================================
# REQUEST SIZE LIMIT MIDDLEWARE
# ============================================================

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE_BYTES:
                    log_security(
                        "oversized_request",
                        detail=f"size={size} max={MAX_REQUEST_SIZE_BYTES}",
                        severity="WARNING"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Request too large",
                            "max_size_bytes": MAX_REQUEST_SIZE_BYTES,
                            "max_size_mb": round(MAX_REQUEST_SIZE_BYTES / 1000000, 1)
                        }
                    )
            except ValueError:
                pass
        return await call_next(request)


# ============================================================
# IP RATE LIMIT MIDDLEWARE
# ============================================================

class IPRateLimitMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = ["/health", "/status", "/", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        path = str(request.url.path)
        if path in self.EXEMPT_PATHS:
            return await call_next(request)
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        if not record_ip_request(client_ip):
            log_security("ip_rate_limit_blocked", detail=f"ip={client_ip[:20]}", severity="WARNING")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests from this IP address",
                    "retry_after": "60 seconds",
                    "message": "Please slow down your requests"
                },
                headers={"Retry-After": "60"}
            )
        return await call_next(request)


# ============================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    SKIP_LOG_PATHS = ["/health", "/status"]

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        api_key = request.headers.get("x-api-key", "")
        client_ip = request.client.host if request.client else "unknown"
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        path = str(request.url.path)
        if path not in self.SKIP_LOG_PATHS:
            log_request(
                method=request.method,
                path=path,
                api_key=api_key,
                status=response.status_code,
                duration_ms=duration_ms,
                ip=client_ip
            )
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        response.headers["X-Powered-By"] = "KRONYX"
        return response


# ============================================================
# TIMEOUT MIDDLEWARE
# ============================================================

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=REQUEST_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            log_warning(f"Request timeout after {REQUEST_TIMEOUT_SECONDS}s: {request.url.path}")
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Request timeout",
                    "message": f"Request took longer than {REQUEST_TIMEOUT_SECONDS} seconds",
                    "timeout_seconds": REQUEST_TIMEOUT_SECONDS
                }
            )


# ============================================================
# CORS PREFLIGHT MIDDLEWARE
# ============================================================

class CORSLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return JSONResponse(
                status_code=200,
                content={"message": "OK"},
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, X-API-Key, Authorization",
                    "Access-Control-Max-Age": "86400"
                }
            )
        return await call_next(request)
