"""
Google Drive Service.
Handles uploading task attachments to Google Drive using the Service Account credentials
and generating public shareable links.
"""

import os
import json
import mimetypes
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Scopes required for Google Drive API
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]


def upload_attachment_to_drive(attachment_url: str) -> str:
    """
    Uploads a local attachment to Google Drive, sets its permission
    to 'anyone with link' (reader), and returns the public webViewLink.

    Args:
        attachment_url (str): The local/relative attachment path (e.g. '/static/attachments/abc.pdf')

    Returns:
        str: The public Google Drive webViewLink, or the original URL on failure.
    """
    if not attachment_url:
        return "Null"

    # 1. Resolve physical local path
    clean_url = attachment_url.lstrip("/")
    if clean_url.startswith("static/"):
        local_path = os.path.join("app", clean_url)
    else:
        local_path = clean_url

    if not os.path.exists(local_path):
        logger.warning(f"Attachment file not found locally at path: {local_path}")
        return attachment_url

    filename = os.path.basename(local_path)
    logger.info(f"Preparing to upload local attachment to Google Drive: {local_path}")

    try:
        # 2. Authenticate using Service Account credentials
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDS_FILE,
            scopes=SCOPES
        )
        authed_session = AuthorizedSession(creds)

        # 3. Detect MIME type
        mime_type, _ = mimetypes.guess_type(local_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        # 4. Perform Multipart Upload to Google Drive
        metadata = {
            "name": filename,
            "description": "Uploaded by AI Task Scheduler"
        }

        # If a shared folder ID is configured, target that folder so the file inherits owner quota
        if settings.GOOGLE_DRIVE_FOLDER_ID:
            metadata["parents"] = [settings.GOOGLE_DRIVE_FOLDER_ID]


        with open(local_path, "rb") as f:
            file_content = f.read()

        files = {
            "data": ("metadata", json.dumps(metadata), "application/json"),
            "file": (filename, file_content, mime_type)
        }

        logger.info(f"Uploading file '{filename}' ({len(file_content)} bytes) to Google Drive...")
        upload_resp = authed_session.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            files=files
        )

        if upload_resp.status_code != 200:
            resp_body = upload_resp.text
            if "drive.googleapis.com" in resp_body or "disabled" in resp_body.lower():
                logger.error(
                    "❌ Google Drive API is not enabled in your Google Cloud Console project.\n"
                    "👉 PLEASE ENABLE IT by visiting this URL: "
                    "https://console.developers.google.com/apis/api/drive.googleapis.com/overview"
                )
            raise RuntimeError(f"Drive upload failed (status {upload_resp.status_code}): {resp_body}")

        file_data = upload_resp.json()
        file_id = file_data.get("id")
        if not file_id:
            raise RuntimeError(f"No file ID returned in Drive upload response: {file_data}")

        logger.info(f"Successfully uploaded file to Google Drive. ID: {file_id}")

        # 5. Make the file publicly visible to everyone with the link
        logger.info(f"Setting public 'anyone' read permissions for file ID: {file_id}")
        perm_payload = {
            "role": "reader",
            "type": "anyone"
        }
        perm_resp = authed_session.post(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
            json=perm_payload
        )

        if perm_resp.status_code not in (200, 201):
            logger.warning(f"Failed to set public permissions on Google Drive file: {perm_resp.text}")

        # 6. Retrieve the webViewLink
        logger.info(f"Fetching public webViewLink for file ID: {file_id}")
        meta_resp = authed_session.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=webViewLink"
        )
        
        if meta_resp.status_code == 200:
            web_view_link = meta_resp.json().get("webViewLink")
            if web_view_link:
                logger.info(f"Google Drive Link generated successfully: {web_view_link}")
                # Clean up local file to prevent storage bloat since it is now uploaded to Google Drive
                try:
                    if os.path.exists(local_path):
                        os.remove(local_path)
                        logger.info(f"Deleted local attachment file after successful Google Drive upload: {local_path}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete local attachment file: {cleanup_err}")
                return web_view_link

        raise RuntimeError(f"Failed to fetch metadata (status {meta_resp.status_code}): {meta_resp.text}")

    except Exception as e:
        logger.error(f"Failed to upload attachment to Google Drive: {e}", exc_info=True)
        # Return a clean error indicator so the caller can decide to fall back
        raise
