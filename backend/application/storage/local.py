import os
import shutil
import tempfile
from typing import BinaryIO, Optional, Union
from backend.application.storage.base import DocumentStorage
from backend.core.config import settings

class LocalStorageProvider(DocumentStorage):
    """
    Local filesystem storage provider for development and testing.
    Safely isolates files by tenant and prevents directory traversal attacks.
    """

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = os.path.abspath(root_dir or settings.STORAGE_ROOT_DIR)
        os.makedirs(self.root_dir, exist_ok=True)

    def _resolve_path(self, key: str) -> str:
        """
        Resolve a storage key to an absolute filesystem path.
        Guarantees that the resulting path is strictly contained within root_dir.
        """
        # Normalize and remove leading slashes or Windows drive specifiers
        clean_key = os.path.normpath(key).lstrip("/\\")
        target_path = os.path.abspath(os.path.join(self.root_dir, clean_key))

        # Security check: ensure path does not escape storage root
        if not target_path.startswith(self.root_dir + os.sep) and target_path != self.root_dir:
            raise ValueError(f"Security error: Storage key '{key}' escapes root directory.")

        return target_path

    def store(self, key: str, data: Union[bytes, BinaryIO], content_type: Optional[str] = None) -> str:
        target_path = self._resolve_path(key)
        dir_path = os.path.dirname(target_path)
        os.makedirs(dir_path, exist_ok=True)

        # Atomic write via temporary file in same folder, then rename
        with tempfile.NamedTemporaryFile("wb", dir=dir_path, delete=False) as tmp:
            if isinstance(data, bytes):
                tmp.write(data)
            else:
                shutil.copyfileobj(data, tmp)
            tmp_name = tmp.name

        os.replace(tmp_name, target_path)
        return key

    def get(self, key: str) -> bytes:
        target_path = self._resolve_path(key)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Document with key '{key}' not found in storage.")
        with open(target_path, "rb") as f:
            return f.read()

    def get_stream(self, key: str) -> BinaryIO:
        target_path = self._resolve_path(key)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Document with key '{key}' not found in storage.")
        return open(target_path, "rb")

    def delete(self, key: str) -> bool:
        try:
            target_path = self._resolve_path(key)
            if os.path.exists(target_path):
                os.remove(target_path)
            return True
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        try:
            target_path = self._resolve_path(key)
            return os.path.exists(target_path) and os.path.isfile(target_path)
        except Exception:
            return False
