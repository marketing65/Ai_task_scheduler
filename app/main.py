"""
FastAPI application entry point.
Configures CORS, includes routers, and defines health check.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import text, audio, employees, sheets
from app.config import settings

from app.utils.logger import get_logger

logger = get_logger(__name__)
STATIC_DIR = Path(__file__).parent / "static"


# ── Lifespan ────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    # ── Startup ─────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  AI Task Management System — Starting Up")
    logger.info("=" * 60)
    logger.info(f"  Model:   {settings.OPENAI_MODEL}")
    logger.info(f"  Whisper: {settings.WHISPER_MODEL}")
    logger.info(f"  Host:    {settings.HOST}:{settings.PORT}")

    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-api-key-here":
        logger.warning(
            "[WARNING] OPENAI_API_KEY is not configured! "
            "Set it in .env or as an environment variable."
        )
    else:
        logger.info("  API Key: [OK] Configured")

    logger.info("=" * 60)

    yield  # App is running

    # ── Shutdown ────────────────────────────────────────────
    logger.info("AI Task Management System — Shutting Down")


# ── Create FastAPI app ──────────────────────────────────────────

app = FastAPI(
    title="AI Task Management System",
    description=(
        "An AI-powered system that converts voice or text instructions "
        "(Hindi, Hinglish, English) into structured task entries. "
        "Uses OpenAI Whisper for speech-to-text and GPT for intelligent "
        "task extraction with date handling and multilingual support."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ────────────────────────────────────────────

app.include_router(text.router)
app.include_router(audio.router)
app.include_router(employees.router)
app.include_router(sheets.router)



# ── Health Check ────────────────────────────────────────────────


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns the health status of the API.",
)
async def health_check():
    """Check if the API is running and the OpenAI key is configured."""
    api_key_configured = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-api-key-here")

    return {
        "status": "healthy",
        "version": "1.0.0",
        "openai_key_configured": api_key_configured,
        "model": settings.OPENAI_MODEL,
        "whisper_model": settings.WHISPER_MODEL,
    }


# ── Page Routes ─────────────────────────────────────────────────

@app.get(
    "/",
    tags=["System"],
    summary="Dashboard",
    include_in_schema=False,
)
async def dashboard_page():
    """Serve the main dashboard."""
    return FileResponse(STATIC_DIR / "index.html")


# ── Mount static files ──────────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
