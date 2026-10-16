import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

import monitor


class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000

        is_error = response.status_code >= 400
        monitor.record_request(duration_ms, is_error)

        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response