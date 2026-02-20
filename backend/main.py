""" 
Main FastAPI application entry point.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from loguru import logger
import sys

from config import settings
from database.connection import init_db, close_db
from api import auth, study_plan, content, quiz, chat, search, mindmap, analytics

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    settings.log_file,
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI Study Planner API...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Study Planner API...")
    await close_db()
    logger.info("Database connections closed")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered study planning and learning assistant for competitive exams",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Mount static files
from fastapi.staticfiles import StaticFiles
import os
os.makedirs("static/uploads", exist_ok=True)
app.mount("/api/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Validation error occurred"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception: " + str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "An internal server error occurred",
            "detail": str(exc) if settings.debug else "Internal server error"
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to AI Study Planner API",
        "version": settings.app_version,
        "docs": "/api/docs"
    }


@app.get("/api/debug/search-status", tags=["Debug"])
async def debug_search_status():
    """Get search service status."""
    from services.serpapi_search import serpapi_service
    return serpapi_service.get_status()


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(study_plan.router, prefix="/api/study-plan", tags=["Study Plan"])
app.include_router(content.router, prefix="/api/content", tags=["Content"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(mindmap.router, prefix="/api/mindmap", tags=["Mindmap"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
from api import admin, engagement
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(engagement.router, prefix="/api/engagement", tags=["Engagement"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
