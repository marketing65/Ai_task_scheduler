"""
Application configuration.
Loads environment variables and provides typed settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── OpenAI ───────────────────────────────────────────────
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for GPT and Whisper access",
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4.1",
        description="OpenAI model to use for task extraction",
    )
    WHISPER_MODEL: str = Field(
        default="whisper-1",
        description="OpenAI Whisper model for speech-to-text",
    )

    # ── Server ───────────────────────────────────────────────
    HOST: str = Field(default="0.0.0.0", description="Server host")

    PORT: int = Field(default=8000, description="Server port")

    # ── Logging ──────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # ── Audio ────────────────────────────────────────────────
    MAX_AUDIO_SIZE_MB: int = Field(
        default=25,
        description="Maximum audio file size in MB",
    )
    ALLOWED_AUDIO_FORMATS: list[str] = Field(
        default=["mp3", "wav", "m4a", "webm", "ogg", "flac"],
        description="Allowed audio file extensions",
    )

    # ── Google Sheets ─────────────────────────────────────────
    GOOGLE_SHEETS_SPREADSHEET_ID: str = Field(
        default="1qNj25TWKLScZUoh9GsQRBUAZEYPWW3toI8xL8KdVBOA",
        description="Google Sheets spreadsheet ID",
    )
    GOOGLE_SHEETS_CREDS_FILE: str = Field(
        default="app/ai-driven-task-scheduler-4a465b6fdc65.json",
        description="Path to Google Sheets Service Account credentials JSON",
    )
    GOOGLE_TYPE: str = Field(
        default="",
        description="Type for Google Service Account credentials",
    )
    GOOGLE_PROJECT_ID: str = Field(
        default="",
        description="Project ID for Google Service Account",
    )
    GOOGLE_PRIVATE_KEY_ID: str = Field(
        default="",
        description="Private Key ID for Google Service Account",
    )
    GOOGLE_PRIVATE_KEY: str = Field(
        default="",
        description="Private Key for Google Service Account",
    )
    GOOGLE_CLIENT_EMAIL: str = Field(
        default="",
        description="Client Email for Google Service Account",
    )
    GOOGLE_CLIENT_ID: str = Field(
        default="",
        description="Client ID for Google Service Account",
    )
    GOOGLE_DRIVE_FOLDER_ID: str = Field(
        default="",
        description="Optional Google Drive shared folder ID to upload attachments into",
    )

    
    # ── Public URL ───────────────────────────────────────────
    APP_URL: str = Field(
        default="",
        description="Optional public URL of the application to override localhost in exported links",
    )

    def get_google_credentials(self) -> dict | None:
        """
        Constructs and returns Google Service Account credentials dictionary if individual
        environment variables are provided. Returns None otherwise.
        """
        if self.GOOGLE_TYPE and self.GOOGLE_PROJECT_ID and self.GOOGLE_PRIVATE_KEY:
            private_key = self.GOOGLE_PRIVATE_KEY
            if private_key:
                # Support unescaping backslash-n to actual newlines
                private_key = private_key.replace("\\n", "\n")
            
            return {
                "type": self.GOOGLE_TYPE,
                "project_id": self.GOOGLE_PROJECT_ID,
                "private_key_id": self.GOOGLE_PRIVATE_KEY_ID,
                "private_key": private_key,
                "client_email": self.GOOGLE_CLIENT_EMAIL,
                "client_id": self.GOOGLE_CLIENT_ID,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.GOOGLE_CLIENT_EMAIL.replace('@', '%40')}" if self.GOOGLE_CLIENT_EMAIL else "",
                "universe_domain": "googleapis.com"
            }
        return None



# Singleton settings instance
settings = Settings()
