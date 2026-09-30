import os
import re
from typing import Optional, Tuple
from backend.core.config import settings

class DocumentValidationError(ValueError):
    """Raised when an uploaded document fails security, format, or size validation."""
    pass

def sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename.
    Removes path traversal components, replaces dangerous characters,
    and normalizes whitespace and extension.
    """
    if not filename:
        return "document"
    
    # Strip any directory path components (both unix and windows)
    clean_base = os.path.basename(filename.replace("\\", "/"))
    name, ext = os.path.splitext(clean_base)
    
    # Replace any character that is not alphanumeric, underscore, hyphen, or dot
    clean_name = re.sub(r"[^\w\.\- ]", "_", name).strip()
    clean_name = re.sub(r"[\s_]+", "_", clean_name).strip("._")
    
    if not clean_name:
        clean_name = "invoice_document"
        
    # Cap length to prevent filesystem limits
    clean_name = clean_name[:100]
    return f"{clean_name}{ext.lower()}"

def validate_document(
    filename: str,
    content_type: str,
    file_bytes: bytes,
    max_size_bytes: Optional[int] = None,
) -> Tuple[str, str]:
    """
    Validate document size, extension, MIME type, and magic bytes signature.
    Guarantees strict security rejection for dangerous or forged files.
    Returns (sanitized_filename, validated_mime_type).
    """
    max_limit = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES
    size_mb = max_limit // (1024 * 1024)

    # 1. Size Validation
    if not file_bytes or len(file_bytes) == 0:
        raise DocumentValidationError("The uploaded file is empty.")

    if len(file_bytes) > max_limit:
        raise DocumentValidationError(f"File is too large. Please upload a file smaller than {size_mb} MB.")

    # 2. Filename & Extension Validation
    if not filename or not filename.strip():
        raise DocumentValidationError("Filename is required.")

    sanitized = sanitize_filename(filename)
    _, ext = os.path.splitext(sanitized)
    ext = ext.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file format '{ext}'. Only PDF, PNG, and JPEG files are supported."
        )

    # 3. Content-Type Validation
    norm_content_type = (content_type or "").strip().lower()
    # Normalize common jpeg aliases
    if norm_content_type == "image/jpg":
        norm_content_type = "image/jpeg"

    if norm_content_type not in settings.ALLOWED_MIME_TYPES:
        raise DocumentValidationError(
            f"Unsupported content type '{norm_content_type}'. Only PDF, PNG, and JPEG files are supported."
        )

    # 4. Explicit Rejection of Dangerous Executables, Archives, and Scripts
    # Check magic bytes for common malicious / script files
    if file_bytes.startswith(b"MZ"):  # DOS/Windows PE Executable
        raise DocumentValidationError("Security violation: Executable files are strictly forbidden.")
    if file_bytes.startswith(b"PK\x03\x04") or file_bytes.startswith(b"PK\x05\x06"):  # ZIP archive
        raise DocumentValidationError("Security violation: Archive files (ZIP) are not permitted.")
    if file_bytes.startswith(b"Rar!\x1a\x07"):  # RAR archive
        raise DocumentValidationError("Security violation: Archive files (RAR) are not permitted.")
    if file_bytes.startswith(b"\x7fELF"):  # Linux Executable
        raise DocumentValidationError("Security violation: Executable files are strictly forbidden.")
    if file_bytes.startswith(b"#!"):  # Shebang script
        raise DocumentValidationError("Security violation: Script files are strictly forbidden.")

    # Inspect first 1KB for XML/HTML/SVG injections
    header_preview = file_bytes[:1024].lower()
    dangerous_tags = [b"<html", b"<!doctype", b"<svg", b"<?xml", b"<script", b"javascript:"]
    for tag in dangerous_tags:
        if tag in header_preview:
            raise DocumentValidationError("Security violation: HTML, XML, or script content detected in document.")

    # 5. Magic Bytes / Header Signature Verification for Allowed Types
    if ext == ".pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise DocumentValidationError("Invalid PDF file: Missing or corrupted PDF header signature.")
    elif ext == ".png":
        if not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise DocumentValidationError("Invalid PNG file: Missing or corrupted PNG header signature.")
    elif ext in (".jpg", ".jpeg"):
        if not file_bytes.startswith(b"\xff\xd8\xff"):
            raise DocumentValidationError("Invalid JPEG file: Missing or corrupted JPEG header signature.")

    return sanitized, norm_content_type
