"""
Google Sheets Service.
Handles authentication using Google service account JSON and appends task rows.
"""

from datetime import datetime
import gspread
from app.config import settings
from app.models import TaskResponse
from app.services.drive import upload_attachment_to_drive
from app.utils.logger import get_logger

logger = get_logger(__name__)


def export_tasks_to_google_sheet(tasks: list[TaskResponse], base_url: str = None) -> int:
    """
    Authenticate with Google Sheets API and append a list of tasks as new rows.

    The columns are matched exactly in the following order:
    1. 'Timestamp ' (Column A)
    2. 'Requester ' (Column B)
    3. 'Task ' (Column C)
    4. 'Doer ' (Column D)
    5. 'Due date' (Column E)
    6. 'Attachment' (Column F)

    Returns:
        int: The number of successfully exported tasks.
    """
    if not tasks:
        logger.info("No tasks to export to Google Sheets.")
        return 0

    logger.info(f"Initiating Google Sheets export for {len(tasks)} task(s).")

    try:
        # 1. Authenticate using Service Account credentials
        gc = gspread.service_account(filename=settings.GOOGLE_SHEETS_CREDS_FILE)

        # 2. Open the spreadsheet by its ID/Key
        spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID
        logger.info(f"Opening spreadsheet with ID: {spreadsheet_id}")
        sh = gc.open_by_key(spreadsheet_id)

        # 3. Select the first worksheet (default sheet)
        worksheet = sh.get_worksheet(0)
        logger.info(f"Opened worksheet: {worksheet.title}")

        # 4. Fetch headers and dynamically ensure 'Attachment' is column F (6th column)
        headers = [h.strip() for h in worksheet.row_values(1)]
        logger.info(f"Detected Google Sheet columns: {headers}")

        if len(headers) < 6 or headers[5].lower() != "attachment":
            logger.info("Adding 'Attachment' header in Column F...")
            worksheet.update_cell(1, 6, "Attachment")

        # 5. Prepare rows data in the exact order of the columns:
        # Column A: Timestamp
        # Column B: Requester
        # Column C: Task
        # Column D: Doer
        # Column E: Due date
        # Column F: Attachment
        rows_to_append = []
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for task in tasks:
            # Format timestamp: use created_at or default to now
            timestamp = task.created_at or current_time_str
            
            # Format attachment URL: upload to Google Drive, fall back to localhost dynamic URL if Drive fails
            attachment_val = "Null"
            if task.attachment:
                try:
                    logger.info(f"Uploading attachment {task.attachment} to Google Drive...")
                    drive_link = upload_attachment_to_drive(task.attachment)
                    attachment_val = drive_link
                except Exception as drive_err:
                    logger.warning(
                        f"Google Drive upload failed. Falling back to absolute local link: {drive_err}"
                    )
                    # Fall back to localhost/base_url link
                    if task.attachment.startswith("http"):
                        attachment_val = task.attachment
                    elif base_url:
                        rel_path = task.attachment if task.attachment.startswith("/") else f"/{task.attachment}"
                        attachment_val = f"{base_url}{rel_path}"
                    else:
                        attachment_val = task.attachment

            
            row = [
                timestamp,
                task.requester_name or "",
                task.task_description or "",
                task.doer_name or "",
                task.due_date or "",
                attachment_val
            ]
            rows_to_append.append(row)

        # 6. Perform a single batch append of all rows for high performance
        logger.info(f"Appending {len(rows_to_append)} row(s) to sheet...")
        worksheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        logger.info("Successfully appended all task rows to Google Sheet.")
        
        # Clean up any local attachment files immediately after successful sheet sync
        import os
        for task in tasks:
            if task.attachment and not task.attachment.startswith("http"):
                try:
                    clean_url = task.attachment.lstrip("/")
                    if clean_url.startswith("static/"):
                        local_path = os.path.join("app", clean_url)
                    else:
                        local_path = clean_url
                    
                    if os.path.exists(local_path):
                        os.remove(local_path)
                        logger.info(f"Auto-deleted local file after task sheet assignment: {local_path}")
                except Exception as clean_err:
                    logger.warning(f"Could not delete attachment file {task.attachment} after sync: {clean_err}")
        
        return len(rows_to_append)

    except Exception as e:
        logger.error(f"Failed to export tasks to Google Sheet: {e}", exc_info=True)
        raise RuntimeError(f"Google Sheets Export Error: {str(e)}")
