import gspread
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("final_test")

try:
    logger.info("Checking reconstructed Google Credentials...")
    creds_dict = settings.get_google_credentials()
    if creds_dict:
        logger.info("Successfully reconstructed credentials from memory!")
        logger.info(f"Project ID: {creds_dict['project_id']}")
        logger.info(f"Client Email: {creds_dict['client_email']}")
        
        logger.info("Attempting gspread authentication from dict...")
        gc = gspread.service_account_from_dict(creds_dict)
        sh = gc.open_by_key("1qNj25TWKLScZUoh9GsQRBUAZEYPWW3toI8xL8KdVBOA")
        logger.info(f"SUCCESS! Spreadsheet connected successfully: {sh.title}")
    else:
        logger.error("Failed to reconstruct credentials! Verify your .env variables.")
except Exception as e:
    logger.error("Authentication failed!", exc_info=True)
