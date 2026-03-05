"""
FastAPI Middleware: request_id pro Request (ContextVar), optional X-Request-ID Response-Header.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .context import bind_request_id, reset_request_id


async def debug_request_id_middleware(request: Request, call_next):
    """Setzt request_id für jeden Request (ContextVar), setzt X-Request-ID im Response-Header."""
    token = bind_request_id()
    try:
        response = await call_next(request)
        try:
            from .context import get_request_id
            rid = get_request_id()
            if rid and hasattr(response, "headers"):
                response.headers["X-Request-ID"] = str(rid)
        except Exception:
            pass
        return response
    finally:
        reset_request_id(token)
