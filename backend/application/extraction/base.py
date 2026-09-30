from abc import ABC, abstractmethod
from typing import Optional
from backend.application.extraction.schemas import GeminiExtractionResponse

class ExtractionError(Exception):
    """Base exception for all invoice extraction failures."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class TransientExtractionError(ExtractionError):
    """
    Temporary or recoverable extraction failure (e.g. rate limit, timeout, service unavailable).
    Safe to retry with exponential backoff.
    """
    pass

class PermanentExtractionError(ExtractionError):
    """
    Non-recoverable failure (e.g. invalid credentials, corrupted document, client error).
    Must NOT be retried.
    """
    pass

class InvoiceExtractor(ABC):
    """
    Abstract interface for invoice data extractors.
    Allows swappable implementations (Gemini, Mock, etc.).
    """

    @abstractmethod
    def extract(
        self,
        document_bytes: bytes,
        mime_type: str,
        filename: str,
    ) -> GeminiExtractionResponse:
        """
        Extract structured invoice header and line items from document bytes.
        
        Args:
            document_bytes: Raw bytes of the PDF or image.
            mime_type: MIME type (application/pdf, image/png, image/jpeg).
            filename: Original file name for logging / context.
            
        Returns:
            GeminiExtractionResponse matching the strict Pydantic extraction schema.
            
        Raises:
            TransientExtractionError: If network/service fails temporarily.
            PermanentExtractionError: If input/auth is fatally flawed.
        """
        pass
