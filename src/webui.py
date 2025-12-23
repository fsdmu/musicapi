"""Web UI for adding YouTube albums and artists to MeTube."""
import logging

import src.logging_config  # initialize logging

from nicegui import ui

from src.me_tube_connector import MeTubeConnector
from src.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


mt_connector = MeTubeConnector(base_url=None)
db_connector = mt_connector.db_connector

ui.label('Enter YouTube URL here:')
url_input = ui.input(placeholder='YouTube URL')

auto_download_toggle = ui.switch("Auto Download artists' future albums", value=False)
add_without_download = ui.switch("Add artist without download", value=False)


def on_submit():
    try:
        url = str(url_input.value).strip()
        urls = None
        if not url:
            ui.notify('Please enter a YouTube URL', color='negative')
            return
        if not "youtube.com" in url:
            ui.notify('Please enter a valid YouTube Music URL', color='negative')
            return
        if "channel" in url:
            urls = YoutubeAlbumFetcher.get_album_ids(url)
            db_connector.add_artist(url)
            if auto_download_toggle.value:
                db_connector.add_auto_download_artist(url)
            for album_url in urls:
                database_album_id = db_connector.add_album(album_url)
                logger.info(f'Added album {album_url} with ID {database_album_id} for artist {url}')

                songs = YoutubeAlbumFetcher.get_album_songs(album_url.split("list=")[1])
                for song_url in songs:
                    database_song_id = db_connector.add_song(song_url)
                    logger.info(f'Added song {song_url} with ID {database_song_id} for album {album_url}')

        elif not "playlist" in url and not "watch" in url:
            ui.notify('Please enter a valid YouTube video, playlist, or channel URL', color='negative')
            return
        if not add_without_download.value:
            mt_connector.queue_download(urls or url, add_without_download=add_without_download.value)

        url_input.value = ''

    except Exception as e:
        ui.notify(f'Error: {e}', color='negative')
        return

ui.button('Submit', on_click=on_submit)

ui.run(host='0.0.0.0', port=8080)

