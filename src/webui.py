from nicegui import ui

from me_tube_connector import MeTubeConnector
from youtube_album_fetcher import YoutubeAlbumFetcher


connector = MeTubeConnector(base_url=None)

ui.label('Enter YouTube URL here:')

# use a widget reference so we can read the value later
url_input = ui.input(placeholder='YouTube URL')

def on_submit():
    urls = url_input.value.strip()
    if not urls:
        ui.notify('Please enter a YouTube URL', color='negative')
        return
    if not "music.youtube.com" in urls:
        ui.notify('Please enter a valid YouTube Music URL', color='negative')
        return
    if "channel" in urls:
        urls = YoutubeAlbumFetcher.get_album_ids(urls)
    elif not "playlist" in urls and not "watch" in urls:
        ui.notify('Please enter a valid YouTube video, playlist, or channel URL', color='negative')
        return
    connector.queue_download(urls)

# single, valid button call
ui.button('Submit', on_click=on_submit)

ui.run()
