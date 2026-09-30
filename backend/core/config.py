import os
from typing import Set
from dotenv import load_dotenv

# Automatically load environment variables from .env in the project root
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))
load_dotenv()

class Settings:
    # 10 MB maximum upload size (configurable via env var MAX_UPLOAD_SIZE_BYTES)
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))
    
    # Root storage directory for uploaded documents
    STORAGE_ROOT_DIR: str = os.getenv(
        "STORAGE_ROOT_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
    )
    
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".png", ".jpg", ".jpeg"}
    ALLOWED_MIME_TYPES: Set[str] = {"application/pdf", "image/png", "image/jpeg"}

    # Gemini & Invoice Extraction Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    EXTRACTION_PROVIDER: str = os.getenv("EXTRACTION_PROVIDER", "gemini")
    EXTRACTION_TIMEOUT_SECONDS: int = int(os.getenv("EXTRACTION_TIMEOUT_SECONDS", "30"))
    EXTRACTION_MAX_RETRIES: int = int(os.getenv("EXTRACTION_MAX_RETRIES", "2"))

settings = Settings()
