import json
import logging
import time
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.core.config import settings
from backend.application.extraction.base import (
    InvoiceExtractor,
    ExtractionError,
    TransientExtractionError,
    PermanentExtractionError,
)
from backend.application.extraction.schemas import GeminiExtractionResponse
from backend.application.extraction.prompts import INVOICE_EXTRACTION_SYSTEM_PROMPT

logger = logging.getLogger("ap_control.extraction.gemini")

class GeminiInvoiceExtractor(InvoiceExtractor):
    """
    Production Gemini invoice extraction provider using official google-genai SDK.
    Supports multimodal PDF, PNG, and JPEG documents with strict Pydantic JSON schemas.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.max_retries = max_retries if max_retries is not None else settings.EXTRACTION_MAX_RETRIES
        self.timeout_seconds = timeout_seconds or settings.EXTRACTION_TIMEOUT_SECONDS

        if not self.api_key:
            logger.warning("GeminiInvoiceExtractor initialized without GEMINI_API_KEY.")

    def _get_client(self) -> genai.Client:
        if not self.api_key:
            raise PermanentExtractionError(
                "Gemini extraction is unavailable because GEMINI_API_KEY is not configured.",
                details={"reason": "MISSING_API_KEY"}
            )
        try:
            return genai.Client(api_key=self.api_key)
        except Exception as e:
            raise PermanentExtractionError(f"Failed to initialize Gemini client: {str(e)}")

    def extract(
        self,
        document_bytes: bytes,
        mime_type: str,
        filename: str,
    ) -> GeminiExtractionResponse:
        client = self._get_client()

        if mime_type not in settings.ALLOWED_MIME_TYPES:
            raise PermanentExtractionError(
                f"Unsupported MIME type for extraction: {mime_type}. Expected PDF, PNG, or JPEG.",
                details={"mime_type": mime_type}
            )

        if not document_bytes or len(document_bytes) == 0:
            raise PermanentExtractionError(
                "Cannot extract from empty document bytes.",
                details={"filename": filename}
            )

        # Prepare multimodal document part
        doc_part = types.Part.from_bytes(data=document_bytes, mime_type=mime_type)

        config = types.GenerateContentConfig(
            system_instruction=INVOICE_EXTRACTION_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=GeminiExtractionResponse,
            temperature=0.0,
        )

        attempts = 0
        backoff_sec = 1.0

        while attempts <= self.max_retries:
            attempts += 1
            try:
                start_t = time.perf_counter()
                logger.info(
                    f"event=gemini_extraction_attempt attempt={attempts}/{self.max_retries + 1} "
                    f"model={self.model_name} filename={filename} mime_type={mime_type} "
                    f"size_bytes={len(document_bytes)}"
                )

                response = client.models.generate_content(
                    model=self.model_name,
                    contents=[doc_part, "Extract the invoice details as structured JSON."],
                    config=config,
                )

                duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
                logger.info(f"event=gemini_extraction_success duration_ms={duration_ms} attempts={attempts}")

                raw_text = response.text
                if not raw_text:
                    raise TransientExtractionError(
                        "Gemini returned an empty response.",
                        details={"status": "EMPTY_RESPONSE"}
                    )

                # Validate with Pydantic
                try:
                    return GeminiExtractionResponse.model_validate_json(raw_text)
                except Exception as ve:
                    logger.error(f"event=gemini_schema_validation_failed error={str(ve)}")
                    raise PermanentExtractionError(
                        f"Gemini output could not be validated against the extraction schema: {str(ve)}",
                        details={"validation_error": str(ve)}
                    )

            except APIError as api_err:
                status_code = getattr(api_err, "code", 500)
                err_msg = str(api_err)

                # Transient errors: 429 (quota/rate limit), 503 (service unavailable), 504 (gateway timeout)
                if status_code in (429, 500, 502, 503, 504):
                    logger.warning(
                        f"event=gemini_transient_error status_code={status_code} "
                        f"attempt={attempts}/{self.max_retries + 1} will_retry={attempts <= self.max_retries}"
                    )
                    if attempts <= self.max_retries:
                        time.sleep(backoff_sec)
                        backoff_sec *= 2.0
                        continue
                    raise TransientExtractionError(
                        f"Gemini extraction service is temporarily unavailable ({status_code}). Please retry.",
                        details={"status_code": status_code, "error": err_msg}
                    )
                else:
                    # Permanent client errors (400 bad request, 401 unauthenticated, 403 forbidden)
                    logger.error(f"event=gemini_permanent_error status_code={status_code}")
                    raise PermanentExtractionError(
                        f"Gemini API request failed ({status_code}).",
                        details={"status_code": status_code}
                    )

            except (TransientExtractionError, PermanentExtractionError):
                raise
            except Exception as e:
                # Other connection / network errors
                err_str = str(e)
                logger.warning(
                    f"event=gemini_network_error error={err_str} "
                    f"attempt={attempts}/{self.max_retries + 1} will_retry={attempts <= self.max_retries}"
                )
                if attempts <= self.max_retries:
                    time.sleep(backoff_sec)
                    backoff_sec *= 2.0
                    continue
                raise TransientExtractionError(
                    f"Failed to communicate with Gemini API: {err_str}",
                    details={"error": err_str}
                )

        raise TransientExtractionError(
            f"Gemini extraction failed after {self.max_retries + 1} attempts.",
            details={"max_retries": self.max_retries}
        )
