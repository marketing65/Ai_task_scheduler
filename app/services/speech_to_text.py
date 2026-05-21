"""
Speech-to-Text service using OpenAI Whisper API.
Handles audio file transcription for Hindi, Hinglish, and English.
"""

import io
from openai import OpenAI
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy-initialized OpenAI client
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Get or create the OpenAI client (singleton)."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    language: str | None = None,
) -> str:
    """
    Transcribe an audio file to text using OpenAI Whisper API.

    Args:
        audio_bytes: Raw bytes of the audio file.
        filename: Original filename (used to infer format).
        language: Optional ISO-639-1 language hint (e.g., "hi" for Hindi).
                  If None, Whisper auto-detects the language.

    Returns:
        Transcribed text string.

    Raises:
        ValueError: If the audio format is unsupported.
        RuntimeError: If the Whisper API call fails.
    """
    # Validate file extension
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in settings.ALLOWED_AUDIO_FORMATS:
        raise ValueError(
            f"Unsupported audio format: .{extension}. "
            f"Allowed: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
        )

    # Validate file size
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_AUDIO_SIZE_MB:
        raise ValueError(
            f"Audio file too large: {size_mb:.1f}MB. "
            f"Maximum: {settings.MAX_AUDIO_SIZE_MB}MB"
        )

    logger.info(
        f"Transcribing audio: {filename} ({size_mb:.2f}MB), "
        f"language hint: {language or 'auto-detect'}"
    )

    try:
        client = _get_client()

        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename  # Whisper API needs filename for format detection

        # Build API parameters
        params = {
            "model": settings.WHISPER_MODEL,
            "file": audio_file,
            "response_format": "verbose_json",  # verbose_json gives full transcript without truncation
        }

        # Add language hint if provided (helps with Hindi/Hinglish)
        if language:
            params["language"] = language

        # Add prompt hint to improve Hindi/Hinglish recognition
        # Biases Whisper vocabulary and capitalization with standard task vocabulary instead of LLM instructions.
        params["prompt"] = (
            "Namaskar, Mukesh sir. Maine saari tasks, doer name, aur deadlines record kar li hain. "
            "Kal tak MIS team ko report ready karke submit kar dena. Meeting agle hafte (next week) hogi. "
            "Important attachments aur documents dynamic sheets mein upload ho chuke hain."
        )

        response = client.audio.transcriptions.create(**params)

        # verbose_json returns an object with .text; plain text returns a string
        if isinstance(response, str):
            transcript = response.strip()
        else:
            transcript = response.text.strip()

        # ── Handle silence hallucinations / prompt repetitions ──────
        lower_transcript = transcript.lower().strip(" .!?")
        
        # Whisper common hallucinations for silence / low volume
        silence_hallucinations = {
            "thank you", "thanks for watching", "subtitles by", "by subtitles",
            "transcribe every word completely without cutting off",
            "transcribe every word in its entirety without omitting any part",
        }
        
        # If the transcript matches these or is too short/empty
        if not lower_transcript or any(h in lower_transcript for h in silence_hallucinations):
            logger.warning(f"Whisper output identified as silence/hallucination: '{transcript}'")
            return ""

        logger.info(f"Transcription complete: {len(transcript)} characters")
        logger.debug(f"Transcribed text: {transcript[:300]}...")

        return transcript

    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise RuntimeError(f"Speech-to-text transcription failed: {e}") from e
