"""Module for connecting to MeTube API and queuing downloads."""

import json
import os
from typing import List, Optional

import requests

import logging

import src.logging_config  # noqa: F401

from src.database_connector import DatabaseConnector
from src.youtube_handler.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MeTubeConnector:
    """Connector for MeTube API."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        """Initialize MeTubeConnector.

        Args:
            base_url: Base URL for MeTube API. If None, will use the
                ME_TUBE_API_URL environment variable.

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

    def queue_download(
        self,
        url: str | List[str],
        quality: str = "Best",
        download_format: str = "mp3",
        add_without_download: bool = False,
    ) -> Optional[List[requests.Response]]:
        """Queue a download for the given URL(s).

        Args:
            url: A single YouTube URL or a list of URLs to queue for download.
            quality: Desired quality of the download. Default is "Best".
            download_format: Desired download_format of the download. Default is "mp3".
            add_without_download: If True, will add the URL to the
                database without queuing a download.

        Returns:
            A list of responses from the MeTube API if downloads were queued,
                otherwise None.

        """
        if type(url) is str:
            url = [url]
        responses = []
        for single_url in url:

            is_song = "watch" in single_url
            is_playlist = "playlist" in single_url

            if is_playlist:
                album_result = self.db_connector.get_album(single_url)
                if album_result is not None:
                    logger.info(f"Album {single_url} already in database, skipping.")
                    continue

            elif is_song:
                song_result = self.db_connector.get_song(single_url)
                if song_result is not None:
                    logger.info(f"Song {single_url} already in database, skipping.")
                    continue

            if not add_without_download:
                data = {
                    "url": single_url,
                    "quality": quality,
                    "format": download_format,
                }
                req = requests.post(
                    f"{self.base_url}/add",
                    data=json.dumps(data),
                    headers={"Content-Type": "application/json"},
                )
                responses.append(req)
                if req.status_code != 200:
                    logger.error(f"Request failed with status code {req.status_code}")
                    logger.info(f"Response: {req.text}")
                    return None

                logger.info(f"Successfully queued download for URL: {single_url}")

            if is_playlist:
                album_id = single_url.split("list=")[1].split("&")[0]
                self.db_connector.add_album(single_url)
                song_urls = YoutubeAlbumFetcher.get_album_songs(album_id)
                for song_url in song_urls:
                    self.db_connector.add_song(song_url)
            elif is_song:
                self.db_connector.add_song(single_url)
            else:
                raise ValueError(f"Unsupported URL format: {single_url}")
        logger.info("Responses: %s", responses)
        return responses
