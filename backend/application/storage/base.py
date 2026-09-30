from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, Union

class DocumentStorage(ABC):
    """
    Abstract interface for secure document storage.
    Enables swapping between LocalStorageProvider and future cloud providers
    (e.g., S3, Supabase Storage, Azure Blob Storage) without altering ingestion services.
    """

    @abstractmethod
    def store(self, key: str, data: Union[bytes, BinaryIO], content_type: Optional[str] = None) -> str:
        """
        Store document content at key.
        Returns the generated storage key.
        """
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        """
        Retrieve complete document content as raw bytes.
        """
        pass

    @abstractmethod
    def get_stream(self, key: str) -> BinaryIO:
        """
        Retrieve document as a readable binary stream for efficient streaming.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete document at storage key.
        Returns True if deleted or already absent.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Verify if a document exists at the given storage key.
        """
        pass
