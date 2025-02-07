# app/main.py
from fastapi import FastAPI
from app.api.v1.routers import api_router
from app.core.config import settings
from app.db.session import engine
from app.db.models import Base

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
