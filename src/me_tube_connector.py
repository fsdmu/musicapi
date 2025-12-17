import json
import os
from typing import List, Optional

import requests

import logging

from src.database_connector import DatabaseConnector
from src.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MeTubeConnector:
    def __init__(self, base_url: Optional[str]) -> None:
        self.base_url = base_url or os.environ.get("ME_TUBE_API_URL")
        self.db_connector = DatabaseConnector()

    def queue_download(self, url: str | List[str],
                       quality: str = "Best",
                       format: str = "mp3",
                       add_without_download: bool = False) -> Optional[List[requests.Response]]:
        if type(url) == str:
            url = [url]
        responses = []
        for url in url:
            if not add_without_download:
                data = {"url": url, "quality": quality, "format": format}
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

                logger.info(f"Successfully queued download for URL: {url}")
            if "playlist" in url:
                album_id = url.split("list=")[1]
                self.db_connector.add_album(url)
                song_urls = YoutubeAlbumFetcher.get_album_songs(album_id)
                for song_url in song_urls:
                    self.db_connector.add_song(song_url)
            elif "watch" in url:
                self.db_connector.add_song(url)

        return responses
