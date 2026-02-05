"""Module for connecting to MeTube API and queuing downloads."""

import json
import logging
import os

import requests

import src.logging_config  # noqa: F401
from src.database_connector import DatabaseConnector
from src.logging.event_logger import log_event
from src.youtube_handler.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger("app.me_tube_connector")
logger.setLevel(logging.INFO)


class MeTubeConnector:
    """Connector for MeTube API."""

    def __init__(
        self, base_url: str | None = None, session_id: str | None = None
    ) -> None:
        """Initialize MeTubeConnector.

        Args:
            base_url: Base URL for MeTube API. If None, will use the
                ME_TUBE_API_URL environment variable.
            session_id: Optional default session_id to attach to logged events.

        Raises:
            ValueError: If base_url is not provided and ME_TUBE_API_URL
                environment variable is not set.

        """
        self.base_url = base_url or os.environ.get("ME_TUBE_API_URL")
        if self.base_url is None:
            raise ValueError(
                "Base URL for MeTube API must be provided either as an argument "
                "or via the ME_TUBE_API_URL environment variable."
            )
        self.db_connector = DatabaseConnector()
        self.default_session_id = session_id

    @log_event("metube.queue_download")
    def queue_download(
        self,
        url: str | list[str],
        quality: str = "Best",
        download_format: str = "mp3",
        add_without_download: bool = False,
        session_id: str | None = None,
    ) -> list[requests.Response] | None:
        """Queue a download for the given URL(s).

        Args:
            url: A single YouTube URL or a list of URLs to queue for download.
            quality: Desired quality of the download. Default is "Best".
            download_format: Desired download_format of the download. Default is "mp3".
            add_without_download: If True, will add the URL to the
                database without queuing a download.
            session_id: Optional session ID for logging.

        Returns:
            A list of responses from the MeTube API if downloads were queued,
                otherwise None.

        """
        effective_session = session_id or self.default_session_id

        if type(url) is str:
            url = [url]
        responses = []
        for single_url in url:
            response = self._download_url(
                single_url,
                quality,
                download_format,
                add_without_download,
                session_id=effective_session,
            )
            if response is not None:
                responses.append(response)

        return responses

    @log_event("metube._download_url")
    def _download_url(
        self,
        single_url: str,
        quality: str,
        download_format: str,
        add_without_download: bool,
        session_id: str | None = None,
    ) -> requests.Response | None:
        """Download a single URL.

            This only supports individual song and playlist URLs.

        Args:
            single_url: The YouTube URL to queue for download.
            quality: Desired quality of the download.
            download_format: Desired download_format of the download.
            add_without_download: If True, will add the URL to the
                database without queuing a download.
            session_id: Optional session ID for logging.

        Returns:
            The response from the MeTube API if download was queued,
                otherwise None.

        Raises:
            ValueError: If the URL format is unsupported.

        """
        is_song = "watch" in single_url
        is_playlist = "playlist" in single_url

        if is_playlist:
            album_result = self.db_connector.get_album(single_url)
            if album_result is not None:
                return None
        elif is_song:
            song_result = self.db_connector.get_song(single_url)
            if song_result is not None:
                return None
        else:
            raise ValueError(f"Unsupported URL format: {single_url}")

        if not add_without_download:
            response = self._add_to_me_tube(
                single_url,
                quality,
                download_format,
                session_id=session_id,
            )
        else:
            response = None

        if is_playlist:
            if "list=" not in single_url:
                raise ValueError(f"Invalid playlist URL: {single_url}")

            album_id = single_url.split("list=")[1].split("&")[0]
            self.db_connector.add_album(single_url)
            song_urls = YoutubeAlbumFetcher.get_album_songs(
                album_id, session_id=session_id
            )
            for song_url in song_urls:
                self.db_connector.add_song(song_url)
        elif is_song:
            self.db_connector.add_song(single_url)

        return response

    @log_event("metube._add_to_me_tube")
    def _add_to_me_tube(
        self,
        single_url: str,
        quality: str,
        download_format: str,
        session_id: str | None = None,  # noqa
    ) -> requests.Response | None:
        """Add URL to MeTube without database checks.

        Args:
            single_url: The YouTube URL to queue for download.
            quality: Desired quality of the download.
            download_format: Desired download_format of the download.
            session_id: Optional session ID for logging.

        Returns:
            The response from the MeTube API if download was queued,
                otherwise None.

        """
        data = {
            "url": single_url,
            "quality": quality,
            "format": download_format,
        }
        response = requests.post(
            f"{self.base_url}/add",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            return None
        return response
