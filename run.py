"""
Entry point for the AI Task Management System.
Starts the FastAPI server using uvicorn.
"""

import uvicorn
from app.config import settings


def main():
    """Launch the application server."""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
