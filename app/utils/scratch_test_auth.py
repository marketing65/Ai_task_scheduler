import gspread
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_auth")

try:
    logger.info("Attempting gspread authentication...")
    gc = gspread.service_account(filename="app/ai-driven-task-scheduler-4a465b6fdc65.json")
    sh = gc.open_by_key("1qNj25TWKLScZUoh9GsQRBUAZEYPWW3toI8xL8KdVBOA")
    logger.info(f"Success! Spreadsheet opened: {sh.title}")
except Exception as e:
    logger.error("Authentication failed!", exc_info=True)
