"""Handler for downloading music from YouTube."""

import logging

import src.logging_config  # noqa: F401
from src.database_connector import DatabaseConnector
from src.download_handler_base import DownloadHandlerBase
from src.logging.event_logger import log_event
from src.youtube_handler.me_tube_connector import MeTubeConnector
from src.youtube_handler.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger("app.yt_download_handler")
logger.setLevel(logging.INFO)


@log_event("youtube.album.added")
def _log_added_album(
    album_url: str,
    database_album_id: int,
    channel_url: str,
    session_id: str | None = None,
) -> dict[str, str | int]:
    """Log the addition of an album to the database.

    Args:
        album_url: The URL of the album that was added.
        database_album_id: The ID of the album in the database.
        channel_url: The URL of the channel the album belongs to.
        session_id: Optional session ID to attach to the logged event.

    Returns:
        A dict containing the logged information about the added album.
    """
    return {
        "album_url": album_url,
        "database_album_id": database_album_id,
        "channel_url": channel_url,
    }


@log_event("youtube.song.added")
def _log_added_song(
    song_url: str,
    database_song_id: int,
    album_url: str | None,
    session_id: str | None = None,
) -> dict[str, str | int | None]:
    """Log the addition of a song to the database.

    Args:
        song_url: The URL of the song that was added.
        database_song_id: The ID of the song in the database.
        album_url: The URL of the album the song belongs to, if applicable.
        session_id: Optional session ID to attach to the logged event.

    Returns:
        A dict containing the logged information about the added song.

    """
    return {
        "song_url": song_url,
        "database_song_id": database_song_id,
        "album_url": album_url,
    }


class YoutubeDownloadHandler(DownloadHandlerBase):
    """Handler for downloading music from YouTube."""

    def __init__(self, db_connector: DatabaseConnector) -> None:
        """Initialize YoutubeDownloadHandler.

        Args:
            db_connector: An instance of DatabaseConnector for database operations.

        """
        self.mt_connector = MeTubeConnector()
        self.db_connector = db_connector

    @log_event("youtube.download")
    def download(
        self,
        url: str,
        auto_download: bool = False,
        download_format: str = "mp3",
        quality: str = "Best",
        session_id: str | None = None,
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
            session_id: Optional session ID to attach to logged events.
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
                session_id=session_id,
            )
        elif "playlist" in url or "watch?v=" in url:
            self.mt_connector.queue_download(
                url,
                quality=quality,
                download_format=download_format,
                add_without_download=add_without_download,
                session_id=session_id,
            )
        else:
            raise ValueError(f"Unsupported YouTube URL format: {url}")

    @log_event("youtube.handle_channel")
    def _handle_channel_url(
        self,
        channel_url: str,
        auto_download: bool,
        quality: str,
        download_format: str,
        add_without_download: bool = False,
        session_id: str | None = None,
    ) -> None:
        """Handle adding a YouTube channel URL to the database.

        Args:
            channel_url: The YouTube channel URL.
            auto_download: Whether to mark the artist for auto-download.
            quality: The desired quality for the downloads.
            download_format: The desired download_format for the downloads.
            add_without_download: If True, will add albums to the database
                without queuing downloads. Default is False.
            session_id: is accepted and propagated to YoutubeAlbumFetcher
                and MeTubeConnector.

        """
        album_urls = YoutubeAlbumFetcher.get_album_ids(
            channel_url, session_id=session_id
        )
        self.db_connector.add_artist(channel_url, auto_download=auto_download)
        for album_url in album_urls:
            try:
                self.mt_connector.queue_download(
                    album_url,
                    quality=quality,
                    download_format=download_format,
                    add_without_download=add_without_download,
                    session_id=session_id,
                )

            except Exception as e:
                raise RuntimeError(
                    f"Error queuing download for album {album_url}: {e}"
                ) from e

            database_album_id = self.db_connector.add_album(album_url)

            if database_album_id is None:
                logger.warning(
                    f"Failed to add album {album_url} to database "
                    f"for channel {channel_url}"
                )
                continue

            actual_id = (
                database_album_id[0]
                if hasattr(database_album_id, "__getitem__")
                else database_album_id
            )
            _log_added_album(album_url, actual_id, channel_url, session_id=session_id)

            songs = YoutubeAlbumFetcher.get_album_songs(
                album_url.split("list=")[1], session_id=session_id
            )
            for song_url in songs:
                database_song_id = self.db_connector.add_song(song_url)

                if database_song_id is None:
                    logger.warning(
                        f"Failed to add song {song_url} to database "
                        f"for album {album_url}"
                    )
                    continue

                actual_id = (
                    database_song_id[0]
                    if hasattr(database_song_id, "__getitem__")
                    else database_song_id
                )
                _log_added_song(song_url, actual_id, album_url, session_id=session_id)

    def get_warning(self, url: str) -> str | None:
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
