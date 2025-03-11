# middleware/logging.py
from fastapi import Request
import json
from starlette.responses import JSONResponse
from typing import Callable
import logging

logger = logging.getLogger(__name__)


async def debug_middleware(request: Request, call_next: Callable):
    """Debug middleware that preserves response body"""

    # Log request details
    print("\n=== Incoming Request ===")
    print(f"Method: {request.method}")
    print(f"Path: {request.url.path}")
    print(f"Headers: {dict(request.headers)}")

    # Log request body for POST/PUT requests
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                try:
                    json_body = json.loads(body)
                    print(f"Request body: {json.dumps(json_body, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Request body: {body.decode()}")
        except Exception as e:
            print(f"Could not read request body: {str(e)}")

    # Log registered routes
    print("\nRegistered routes:")
    for route in request.app.routes:
        print(f"{route.methods} {route.path}")

    # Get response
    response = await call_next(request)

    print("\n=== Response ===")
    print(f"Status: {response.status_code}")

    # Only try to log JSON responses without modifying them
    if isinstance(response, JSONResponse):
        print(f"Response body: {json.dumps(response.body.decode(), indent=2)}")

    print("=== End Request ===\n")
    return response
