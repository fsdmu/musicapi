"""Handler for downloading music from YouTube."""

import logging
from typing import Optional

import src.logging_config  # noqa: F401

from src.database_connector import DatabaseConnector
from src.download_handler_base import DownloadHandlerBase
from src.youtube_handler.me_tube_connector import MeTubeConnector
from src.youtube_handler.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class YoutubeDownloadHandler(DownloadHandlerBase):
    """Handler for downloading music from YouTube."""

    def __init__(self, db_connector: DatabaseConnector) -> None:
        """Initialize YoutubeDownloadHandler.

        Args:
            db_connector: An instance of DatabaseConnector for database operations.

        """
        self.mt_connector = MeTubeConnector()
        self.db_connector = db_connector

    def download(
        self,
        url: str,
        auto_download: bool = False,
        download_format: str = "mp3",
        quality: str = "Best",
        **kwargs,
    ) -> None:
        """Download music from a YouTube URL.

        Args:
            url: The YouTube URL to download from.
            auto_download: Whether to mark an artist for auto-download.
                This is only applicable if the URL is a channel URL. Default is False.
            download_format: The desired download_format for the download.
                Default is "mp3".
            quality: The desired quality for the download. Default is "Best".
            **kwargs: Additional keyword arguments.

        Raises:
            ValueError: If the URL format is unsupported.

        """
        add_without_download = kwargs.get("add_without_download", False)

        if "channel" in url:
            self._handle_channel_url(
                url,
                auto_download,
                quality=quality,
                download_format=download_format,
            )
        elif "playlist" in url or "watch?v=" in url:
            self.mt_connector.queue_download(
                url,
                quality=quality,
                download_format=download_format,
                add_without_download=add_without_download,
            )
        else:
            error = f"Unsupported YouTube URL format: {url}"
            logger.error(error)
            raise ValueError(error)

    def _handle_channel_url(
        self,
        channel_url: str,
        auto_download: bool,
        quality: str,
        download_format: str,
        add_without_download: bool = False,
    ) -> None:
        """Handle adding a YouTube channel URL to the database.

        Args:
            channel_url: The YouTube channel URL.
            auto_download: Whether to mark the artist for auto-download.
            add_without_download: If True, will add albums to the database
                without queuing downloads. Default is False.

        """
        album_urls = YoutubeAlbumFetcher.get_album_ids(channel_url)
        self.db_connector.add_artist(channel_url, auto_download=auto_download)
        for album_url in album_urls:
            try:
                self.mt_connector.queue_download(
                    album_url,
                    quality=quality,
                    download_format=download_format,
                    add_without_download=add_without_download,
                )

            except Exception as e:
                raise RuntimeError(
                    f"Error queuing download for album {album_url}: {e}"
                ) from e

            database_album_id = self.db_connector.add_album(album_url)
            logger.info(
                f"Added album {album_url} with ID {database_album_id} "
                f"for artist {channel_url}"
            )

            songs = YoutubeAlbumFetcher.get_album_songs(album_url.split("list=")[1])
            for song_url in songs:
                database_song_id = self.db_connector.add_song(song_url)
                logger.info(
                    f"Added song {song_url} with ID {database_song_id} "
                    f"for album {album_url}"
                )

    def get_warning(self, url: str) -> Optional[str]:
        """Get a warning message for the given URL, if applicable.

        Args:
            url: The YouTube URL to check.

        Returns:
            A warning message if applicable, otherwise None.

        """
        if "youtube.com" in url and "music.youtube.com" not in url:
            return (
                "Using youtube.com links instead of music.youtube.com links "
                "is discouraged."
            )
        return None
