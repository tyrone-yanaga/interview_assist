# middleware/logging.py
import logging
from fastapi import Request

logger = logging.getLogger(__name__)


async def debug_middleware(request: Request, call_next):
    logger.debug(f"==== Incoming Request ====")
    logger.debug(f"Method: {request.method}")
    logger.debug(f"Path: {request.url.path}")
    logger.debug(f"Headers: {dict(request.headers)}")

    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                logger.debug(f"Request Body: {body.decode()}")
    except Exception as e:
        logger.debug(f"Could not log request body: {str(e)}")

    response = await call_next(request)

    logger.debug("==== Response ====")
    logger.debug(f"Status Code: {response.status_code}")

    return response
