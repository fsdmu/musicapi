"""Base class for download handlers."""

from abc import ABC, abstractmethod


class DownloadHandlerBase(ABC):
    """Base class for download handlers."""

    @abstractmethod
    def download(
        self,
        url: str,
        get_songs: bool = False,  # make optional default False
        auto_download: bool = False,
        *args,
        session_id: str | None = None,
        **kwargs,
    ) -> None:
        """Download the content from the URL.

        This method should be overridden by subclasses.

        Args:
            url: The URL to download from.
            get_songs: Whether to extract individual songs and not just eps and
                albums when downloading from an artist URL.
            auto_download: Whether to mark the content for auto-download.
            *args: Positional arguments for the download method.
            session_id: Optional session identifier to propagate to downstream calls.
            **kwargs: Keyword arguments for the download method.

        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def get_warning(self, url: str) -> str | None:
        """Get any warnings related to the URL.

        Args:
            url: The URL to check for warnings.

        Returns:
            An optional warning message.

        """
        pass
