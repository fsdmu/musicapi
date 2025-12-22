"""Automatically download albums from artists marked for auto-download."""
import logging
import src.logging_config  # initialize logging

from src.me_tube_connector import MeTubeConnector
from src.database_connector import DatabaseConnector
from src.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():
    """Automatically download albums from artists marked for auto-download."""
    db = DatabaseConnector()
    mt = MeTubeConnector(base_url=None)

    artist_urls = db.get_auto_download_artists()
    for artist_url in artist_urls:
        try:
            album_urls = YoutubeAlbumFetcher.get_album_ids(artist_url)
            mt.queue_download(album_urls)
        except Exception as e:
            logger.error(f"Error processing artist {artist_url}: {e}")

if __name__ == "__main__":
    main()
