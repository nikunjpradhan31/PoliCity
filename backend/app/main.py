"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.logging import setup_logging, logger
from app.core.middleware import setup_cors, RequestLoggingMiddleware
from app.api.routes import health, potholes, budget, optimization, reports


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    try:
        await connect_to_mongo()
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await close_mongo_connection()
    logger.info("Closed MongoDB connection")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Municipal pothole optimization platform API",
    lifespan=lifespan,
)

# Setup middleware
setup_cors(app)
app.add_middleware(RequestLoggingMiddleware)


# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(potholes.router, prefix="/api/v1")
app.include_router(budget.router, prefix="/api/v1")
app.include_router(optimization.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get(
    "/",
    summary="Root endpoint",
    description="Returns API information",
)
async def root():
    """Root endpoint returning API information."""
    return JSONResponse(
        content={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
