"""
FastAPI middleware that enforces the current mitigation level.

Runs on EVERY incoming request BEFORE it reaches the endpoint.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from mitigation import state, limiter, LEVELS, is_enabled         # ✅

# Paths that MUST stay reachable even during aggressive mitigation.
# If /metrics were rate-limited, our own mitigation_loop would get 429'd
# and the level would get stuck forever. This is a critical safety net.
EXEMPT_PATHS = {
    "/metrics",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class MitigationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 1. Bypass internal endpoints entirely
        if request.url.path in EXEMPT_PATHS or not is_enabled():
            return await call_next(request)

        # 2. Read current level (fast, in-memory)
        level, _reason = state.get()
        config = LEVELS[level]
        limit = config["rate_limit"]

        # 3. Extract client IP (works with Docker bridge network)
        ip = request.client.host if request.client else "unknown"

        # 4. Ask the limiter
        allowed, why = limiter.check(ip, limit)

        # 5. Deny → return 429 with useful info
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate limited",
                    "detail": why,
                    "mitigation_level": level,
                    "retry_after_sec": 1,
                },
                headers={
                    "Retry-After": "1",
                    "X-Mitigation-Level": level,
                },
            )

        # 6. Allow → forward to endpoint, decorate response
        response = await call_next(request)
        response.headers["X-Mitigation-Level"] = level
        if limit is not None:
            response.headers["X-Rate-Limit"] = str(limit)
        return response