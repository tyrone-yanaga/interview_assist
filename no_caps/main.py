# app/main.py
from fastapi import FastAPI
from api.routers import api_router
from core.config import settings
from db.session import engine, Base
import logging
from middleware.logging import debug_middleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Add debug middleware
app.middleware("http")(debug_middleware)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
