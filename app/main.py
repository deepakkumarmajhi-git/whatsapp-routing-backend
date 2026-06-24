from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.config import settings
from app.config.database import db_manager
from app.routers import webhook

app = FastAPI(
    title=settings.APP_NAME,
    description="Production backbone routing customer hooks to Next.js and dispatching templates to workers.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    db_manager.connect_to_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    db_manager.close_database_connection()

@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint for Render monitoring."""
    return {"status": "healthy", "database": "connected" if db_manager.db is not None else "disconnected"}

app.include_router(webhook.router)