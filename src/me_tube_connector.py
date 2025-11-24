import json
import os
from typing import List, Optional

import requests

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MeTubeConnector:
    def __init__(self, base_url: Optional[str]) -> None:
        self.base_url = base_url or os.environ.get("ME_TUBE_API_URL")

    def queue_download(self, url: str | List[str],
                       quality: str = "Best",
                       format: str = "mp3") -> List[requests.Response]:
        if type(url) == str:
            url = [url]
        responses = []
        for single_url in url:
            data = {"url": single_url, "quality": quality, "format": format}
            req = requests.post(
                f"{self.base_url}/add",
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
            )
            responses.append(req)
            if req.status_code != 200:
                logger.error(f"Request failed with status code {req.status_code}")
                logger.info(f"Response: {req.text}")
        return responses
