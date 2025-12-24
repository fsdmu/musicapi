"""Module for handling URL-based download handlers."""

from src.download_handler_base import DownloadHandlerBase
from src.youtube_handler.youtube_download_handler import YoutubeDownloadHandler
from src.database_connector import DatabaseConnector


class UrlHandler:
    """Handler for determining the appropriate download handler based on URL."""

    @staticmethod
    def get_handler(url: str) -> DownloadHandlerBase:
        """Get the appropriate download handler based on the URL format.

        Args:
            url: The URL to get the handler for.

        Returns:
            An instance of a DownloadHandlerBase subclass.

        Raises:
            ValueError: If the URL format is unsupported.

        """
        if "youtube.com" in url:
            db_connector = DatabaseConnector()
            return YoutubeDownloadHandler(db_connector)
        else:
            raise ValueError(f"Unsupported URL format: {url}")
