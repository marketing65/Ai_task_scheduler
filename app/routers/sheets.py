"""
Google Sheets Router.
Exposes API endpoints to export task data into Google Sheets.
"""

from fastapi import APIRouter, HTTPException, Request
from app.config import settings
from app.models import GoogleSheetsExportRequest, ErrorResponse
from app.services.sheets import export_tasks_to_google_sheet
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/sheets", tags=["Google Sheets Integration"])


@router.post(
    "/export",
    summary="Export tasks to Google Sheets",
    description=(
        "Receives a structured list of tasks and appends them "
        "directly into the configured Google Sheets spreadsheet "
        "using Google Service Account credentials."
    ),
    responses={
        200: {
            "description": "Tasks successfully exported",
            "content": {
                "application/json": {
                    "example": {"status": "success", "exported_count": 2}
                }
            }
        },
        500: {"model": ErrorResponse, "description": "Google Sheets export failure"},
    },
)
async def export_to_sheets(request: Request, export_request: GoogleSheetsExportRequest):
    """
    Export tasks into the Google Sheet columns.
    
    Accepts:
        tasks: list of extracted task objects.
    """
    logger.info(f"POST /sheets/export — request received with {len(export_request.tasks)} task(s)")

    if not export_request.tasks:
        raise HTTPException(
            status_code=400,
            detail="Task list cannot be empty.",
        )

    try:
        # Prioritize manual override APP_URL from settings/environment, otherwise fall back to dynamic request base URL
        if settings.APP_URL:
            base_url = settings.APP_URL.rstrip("/")
        else:
            base_url = str(request.base_url).rstrip("/")
        
        exported_count = export_tasks_to_google_sheet(export_request.tasks, base_url=base_url)
        logger.info(f"Successfully exported {exported_count} task(s) to Google Sheets.")
        return {
            "status": "success",
            "exported_count": exported_count
        }

    except RuntimeError as e:
        logger.error(f"Sheets export endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in POST /sheets/export: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during Google Sheets export.",
        )
