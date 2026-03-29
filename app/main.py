"""
BizForge - GenAI-Powered Branding & Business Analytics Platform
Main FastAPI Application Entry Point
"""

import time
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import brand, content, chat, sentiment, design, logo, users, export

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("bizforge")

# Get settings
settings = get_settings()


# Initialize FastAPI application
app = FastAPI(
    title="BizForge API",
    description="GenAI-powered branding and business analytics platform for startups, creators, and small businesses.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Global Exception Handler ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return structured JSON error."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred. Please try again."
        }
    )


# === Request Timing Middleware ===
@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Log request timing for performance monitoring."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    if duration > 2.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.2f}s")
    return response


# === Startup Event ===
@app.on_event("startup")
async def startup_validation():
    """Validate critical configuration on startup."""
    if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key_here":
        logger.warning(
            "⚠️  GROQ_API_KEY is not configured. AI features will fail. "
            "Set it in your .env file."
        )
    else:
        logger.info("✅ GROQ_API_KEY configured")

    if settings.stability_api_key:
        logger.info("✅ STABILITY_API_KEY configured (logo generation enabled)")
    else:
        logger.info("ℹ️  STABILITY_API_KEY not set — logo generation will use placeholder")

    logger.info(f"🚀 BizForge API starting on {settings.host}:{settings.port} (debug={settings.debug})")


# Include API routers
app.include_router(brand.router, prefix=settings.api_prefix, tags=["Brand"])
app.include_router(content.router, prefix=settings.api_prefix, tags=["Content"])
app.include_router(chat.router, prefix=settings.api_prefix, tags=["Chat"])
app.include_router(sentiment.router, prefix=settings.api_prefix, tags=["Sentiment"])
app.include_router(design.router, prefix=settings.api_prefix, tags=["Design"])
app.include_router(logo.router, prefix=settings.api_prefix, tags=["Logo"])
app.include_router(users.router, prefix=settings.api_prefix, tags=["Users"])
app.include_router(export.router, prefix=settings.api_prefix, tags=["Export"])


@app.get("/api/config", tags=["Config"])
async def get_public_config():
    """Returns public configuration for frontend."""
    return {"google_client_id": settings.google_client_id}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "BizForge API",
        "model": settings.model_name
    }


# Mount frontend static files (must be after API routes)
# Resolve path relative to the project root (parent of 'app' directory)
_project_root = Path(__file__).resolve().parent.parent
_frontend_dir = _project_root / "frontend"
app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
