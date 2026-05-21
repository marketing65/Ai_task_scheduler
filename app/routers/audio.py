"""
Audio processing endpoint.
Accepts audio files, transcribes via Whisper, then extracts structured tasks.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from app.models import ProcessingResult, ErrorResponse
from app.services.speech_to_text import transcribe_audio
from app.services.task_extractor import extract_tasks
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Audio Processing"])


@router.post(
    "/process-audio",
    response_model=ProcessingResult,
    summary="Extract tasks from audio input",
    description=(
        "Accepts an audio file (mp3, wav, m4a, webm, ogg, flac). "
        "Transcribes the audio using OpenAI Whisper, then extracts "
        "structured task fields. Supports Hindi, Hinglish, and English audio."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid audio file"},
        500: {"model": ErrorResponse, "description": "Processing error"},
    },
)
async def process_audio(
    audio: UploadFile = File(
        ...,
        description="Audio file (mp3, wav, m4a, webm, ogg, flac)",
    ),
    language: Optional[str] = Form(
        default=None,
        description=(
            "Optional ISO-639-1 language hint. "
            "Use 'hi' for Hindi, 'en' for English. "
            "Leave empty for auto-detection."
        ),
    ),
) -> ProcessingResult:
    """
    Process an audio file and extract structured task(s).

    **Pipeline**: Audio → Whisper STT → GPT Extraction → Structured JSON

    **Supported Formats**: mp3, wav, m4a, webm, ogg, flac

    **Language Hints** (optional):
    - `hi` — Hindi
    - `en` — English
    - Leave blank for auto-detection (works for Hinglish too)
    """
    logger.info(
        f"POST /process-audio — file: {audio.filename}, "
        f"content_type: {audio.content_type}, language: {language}"
    )

    # ── Validate file extension ─────────────────────────────────

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio filename is required.")

    extension = audio.filename.rsplit(".", 1)[-1].lower() if "." in audio.filename else ""
    if extension not in settings.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported audio format: .{extension}. "
                f"Allowed formats: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
            ),
        )

    # ── Read audio bytes ────────────────────────────────────────

    try:
        audio_bytes = await audio.read()
    except Exception as e:
        logger.error(f"Failed to read audio file: {e}")
        raise HTTPException(status_code=400, detail="Could not read the audio file.")

    # ── Validate file size ──────────────────────────────────────

    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Audio file too large: {size_mb:.1f}MB. "
                f"Maximum allowed: {settings.MAX_AUDIO_SIZE_MB}MB."
            ),
        )

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    # ── Step 1: Transcribe ──────────────────────────────────────

    try:
        transcribed_text = await transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename,
            language=language,
        )
        logger.info(f"Transcription result: '{transcribed_text[:100]}...'")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not transcribed_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not transcribe any text from the audio. "
            "Please ensure the audio contains clear speech.",
        )

    # ── Step 2: Extract tasks ───────────────────────────────────

    try:
        result = await extract_tasks(transcribed_text)
        logger.info(
            f"Audio processed → {len(result.tasks)} task(s), "
            f"{result.processing_time_ms:.0f}ms"
        )
        return result

    except RuntimeError as e:
        logger.error(f"Task extraction from audio failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in /process-audio: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the audio.",
        )
