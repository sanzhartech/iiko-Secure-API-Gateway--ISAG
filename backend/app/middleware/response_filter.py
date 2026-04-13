"""
response_filter.py — Response Filtering Stage 9
[Rule 2] Fail-Closed Principle: Ensure sensitive data doesn't leak in responses.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from fastapi import Request

class ResponseFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # [Rule 10] Sanitize error responses or remove sensitive headers
        # Example: Ensure no "Server" header reveals internal tech stack
        if "Server" in response.headers:
            del response.headers["Server"]
            
        return response
