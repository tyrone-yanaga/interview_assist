# app/main.py
from fastapi import FastAPI
from api.routers import api_router
from core.config import settings
from db.session import engine, Base

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
