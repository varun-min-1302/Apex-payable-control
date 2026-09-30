from backend.application.extraction.base import (
    InvoiceExtractor,
    ExtractionError,
    TransientExtractionError,
    PermanentExtractionError,
)
from backend.application.extraction.schemas import (
    ExtractedField,
    ExtractedLineItem,
    GeminiExtractionResponse,
    VendorMatchInfo,
    ExtractionResult,
    InvoiceDraftResponse,
    InvoiceDraftUpdate,
    ConfirmDraftResponse,
)
from backend.application.extraction.gemini import GeminiInvoiceExtractor
from backend.application.extraction.mock import MockInvoiceExtractor

from backend.core.config import settings
import logging

logger = logging.getLogger("ap_control.extraction")

def get_extractor(provider: str = "gemini") -> InvoiceExtractor:
    """Factory helper to obtain an instance of the configured InvoiceExtractor."""
    provider_clean = (provider or "gemini").lower().strip()
    if provider_clean == "mock":
        return MockInvoiceExtractor()
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured; using MockInvoiceExtractor for offline/local development.")
        return MockInvoiceExtractor()
    return GeminiInvoiceExtractor()

__all__ = [
    "InvoiceExtractor",
    "ExtractionError",
    "TransientExtractionError",
    "PermanentExtractionError",
    "ExtractedField",
    "ExtractedLineItem",
    "GeminiExtractionResponse",
    "VendorMatchInfo",
    "ExtractionResult",
    "InvoiceDraftResponse",
    "InvoiceDraftUpdate",
    "ConfirmDraftResponse",
    "GeminiInvoiceExtractor",
    "MockInvoiceExtractor",
    "get_extractor",
]
