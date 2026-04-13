"""
size_validator.py — Request Size Validation Stage 2
[Rule 12] Gateway MUST implement: Max request body size.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

class RequestSizeValidatorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int = 10 * 1024 * 1024):  # Default 10MB
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_upload_size:
                raise HTTPException(status_code=413, detail="Request entity too large")
        
        return await call_next(request)
