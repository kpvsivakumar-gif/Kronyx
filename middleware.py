import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import MAX_REQUEST_SIZE_BYTES, REQUEST_TIMEOUT_SECONDS
from security import record_ip_request, SECURITY_HEADERS
from logger import log_request, log_security


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers[key] = value
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE_BYTES:
                    log_security("oversized_request", detail=f"size={size}")
                    return JSONResponse(status_code=413, content={"error": "Request too large"})
            except ValueError:
                pass
        return await call_next(request)


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        if not record_ip_request(client_ip):
            return JSONResponse(status_code=429, content={"error": "Too many requests from this IP"})
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        api_key = request.headers.get("x-api-key", "")
        response = await call_next(request)
        duration = round((time.time() - start_time) * 1000, 2)
        log_request(method=request.method, path=str(request.url.path), api_key=api_key, status=response.status_code)
        response.headers["X-Response-Time"] = f"{duration}ms"
        return response


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        import asyncio
        try:
            return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            return JSONResponse(status_code=504, content={"error": "Request timeout"})
