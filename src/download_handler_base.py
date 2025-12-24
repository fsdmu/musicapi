"""Base class for download handlers."""

from abc import ABC, abstractmethod
from typing import Optional


class DownloadHandlerBase(ABC):
    """Base class for download handlers."""

    @abstractmethod
    def download(self, url: str, auto_download: bool, *args, **kwargs) -> None:
        """Download the content from the URL.

        This method should be overridden by subclasses.

        Args:
            url: The URL to download from.
            auto_download: Whether to mark the content for auto-download.
            *args: Positional arguments for the download method.
            **kwargs: Keyword arguments for the download method.

        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def get_warning(self, url: str) -> Optional[str]:
        """Get any warnings related to the URL.

        Args:
            url: The URL to check for warnings.

        Returns:
            An optional warning message.

        """
        pass
