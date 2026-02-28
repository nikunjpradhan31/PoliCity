"""
FastAPI application initialization for PoliCity API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.routes import router
from app.db import close_mongo_connection, get_mongo_client
from app.services.mongo import setup_indexes

# Load environment variables
load_dotenv()

# App configuration
APP_NAME: str = os.getenv("APP_NAME", "PoliCity API")
APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# CORS configuration
CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print(f"Starting {APP_NAME} v{APP_VERSION}")
    get_mongo_client()
    
    # Setup workflow indexes
    try:
        await setup_indexes()
        print("Setup workflow database indexes")
    except Exception as e:
        print(f"Failed to setup workflow indexes: {e}")
        
    yield
    # Shutdown
    close_mongo_connection()
    print("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="PoliCity API",
    debug=DEBUG,
    lifespan=lifespan
)

# Configure CORS
cors_origins = [origin.strip() for origin in CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root endpoint - redirects to API info.
    """
    return {
        "message": "Welcome to PoliCity API",
        "version": APP_VERSION,
        "docs": "/docs"
    }


# Run the application
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=DEBUG
    )
