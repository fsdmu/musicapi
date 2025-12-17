import logging

from nicegui import ui

from me_tube_connector import MeTubeConnector
from youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


mt_connector = MeTubeConnector(base_url=None)
db_connector = mt_connector.db_connector

ui.label('Enter YouTube URL here:')
url_input = ui.input(placeholder='YouTube URL')

auto_download_toggle = ui.switch("Auto Download artists' future albums", value=False)
add_without_download = ui.switch("Add artist without auto download", value=False)


def on_submit():
    try:
        url = str(url_input.value).strip()
        urls = None
        if not url:
            ui.notify('Please enter a YouTube URL', color='negative')
            return
        if not "music.youtube.com" in url:
            ui.notify('Please enter a valid YouTube Music URL', color='negative')
            return
        if "channel" in url:
            urls = YoutubeAlbumFetcher.get_album_ids(url)
            database_artist_id = db_connector.get_artist_id(url)
            if database_artist_id is None:
                db_connector.add_artist(url)
            if auto_download_toggle.value:
                db_connector.add_auto_download_artist(url)

        elif not "playlist" in url and not "watch" in url:
            ui.notify('Please enter a valid YouTube video, playlist, or channel URL', color='negative')
            return
        if not add_without_download.value:
            mt_connector.queue_download(urls or url, add_without_download=add_without_download.value)

    except Exception as e:
        ui.notify(f'Error: {e}', color='negative')
        return

ui.button('Submit', on_click=on_submit)

ui.run()
