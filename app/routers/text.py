"""
Text processing endpoint.
Accepts text input (Hindi/Hinglish/English) and returns structured tasks.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
import shutil
from pathlib import Path
import time
from app.models import ProcessTextRequest, ProcessingResult, ErrorResponse
from app.services.task_extractor import extract_tasks
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Text Processing"])


@router.post(
    "/upload-attachment",
    summary="Upload an attachment file",
    description="Uploads a file to be attached to a task and returns the public file URL."
)
async def upload_attachment(file: UploadFile = File(...)):
    """
    Upload a file attachment to the server.
    Saves the file to app/static/attachments/ and returns the relative URL.
    """
    from app.main import STATIC_DIR
    attachments_dir = STATIC_DIR / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepend timestamp to filename to prevent collisions and sanitize
    safe_filename = f"{int(time.time())}_{file.filename}"
    file_path = attachments_dir / safe_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded attachment: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while saving the file."
        )
        
    return {
        "filename": file.filename,
        "url": f"/static/attachments/{safe_filename}"
    }


@router.post(
    "/process-text",
    response_model=ProcessingResult,
    summary="Extract tasks from text input",
    description=(
        "Accepts a text string in Hindi, Hinglish, or English. "
        "Extracts structured task fields including requester, doer, "
        "department, due date, and task description. "
        "Supports multiple tasks in a single input."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Processing error"},
    },
)
async def process_text(request: ProcessTextRequest) -> ProcessingResult:
    """
    Process a text input and extract structured task(s).

    **Supported Languages**: Hindi, Hinglish (Hindi-English mix), English

    **Example Input**:
    ```
    Mukesh sir ne bola Rahul ko HR department mein documents submit karne hain
    aur last date 25 April hai
    ```

    **Returns**: Structured JSON with extracted task fields.
    """
    logger.info(f"POST /process-text — input length: {len(request.text)} chars")

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Input text cannot be empty.",
        )

    try:
        result = await extract_tasks(request.text, attachment_filename=request.attachment)
        logger.info(
            f"Processed text → {len(result.tasks)} task(s), "
            f"{result.processing_time_ms:.0f}ms"
        )
        return result

    except RuntimeError as e:
        logger.error(f"Task extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in /process-text: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the text.",
        )
