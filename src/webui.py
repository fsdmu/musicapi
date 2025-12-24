"""Web UI for adding YouTube albums and artists to MeTube."""

import logging

import src.logging_config  # noqa: F401

from nicegui import ui

from src.me_tube_connector import MeTubeConnector
from src.youtube_album_fetcher import YoutubeAlbumFetcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


mt_connector = MeTubeConnector(base_url=None)
db_connector = mt_connector.db_connector

ui.button(icon="code", on_click=lambda: right_drawer.toggle()).classes(
    "absolute top-2 right-2")

ui.label("Enter YouTube URL here:")
url_input = ui.input(placeholder="YouTube URL")

auto_download_toggle = ui.switch("Auto Download artists' future albums", value=False)


def _handle_channel_url(channel_url: str) -> None:
    """Handle adding a YouTube channel URL to the database.

    Args:
        channel_url: The YouTube channel URL.

    """
    channel_urls = YoutubeAlbumFetcher.get_album_ids(channel_url)
    db_connector.add_artist(channel_url)
    if auto_download_toggle.value:
        db_connector.add_auto_download_artist(channel_url)
    for album_url in channel_urls:
        database_album_id = db_connector.add_album(album_url)
        logger.info(
            f"Added album {album_url} with ID {database_album_id} "
            f"for artist {channel_url}"
        )

        songs = YoutubeAlbumFetcher.get_album_songs(album_url.split("list=")[1])
        for song_url in songs:
            database_song_id = db_connector.add_song(song_url)
            logger.info(
                f"Added song {song_url} with ID {database_song_id} "
                f"for album {album_url}"
            )



async def on_submit():
    """Handle the submission of a YouTube URL."""
    try:
        url = str(url_input.value).strip()
        urls = None
        if not url:
            ui.notify("Please enter a YouTube URL", color="negative")
            return
        if "youtube.com" not in url:
            ui.notify("Please enter a valid YouTube Music URL",
                      color="negative")
            return
        if "music.youtube.com" not in url:
            with ui.dialog() as dialog, ui.card():
                ui.label('Using youtube.com links instead of music.youtube.com links'
                         'is discouraged.\nDo you want to continue?')
                with ui.row():
                    ui.button('Yes', on_click=lambda: dialog.submit('Yes'))
                    ui.button('No', on_click=lambda: dialog.submit('No'))

            result = await dialog
            if result != 'Yes':
                return

        if "channel" in url:
            _handle_channel_url(url)
        elif "playlist" not in url and "watch" not in url:
            ui.notify(
                "Please enter a valid YouTube video, playlist, or channel URL",
                color="negative",
            )
            return
        if not add_without_download.value:
            mt_connector.queue_download(
                urls or url, add_without_download=add_without_download.value,
                format=audio_format.value
            )

        url_input.value = ""

    except Exception as e:
        ui.notify(f"Error: {e}", color="negative")
        return


ui.button("Submit", on_click=on_submit)

with ui.right_drawer(top_corner=True, value=False).style(
        'background-color: #ececec') as right_drawer:
    add_without_download = ui.switch("Add artist to download future albums without "
                                    "queuing downloads now.",
                                     value=False)
    audio_format = ui.select(
        ["mp3", "wav", "flac", "m4a"],
        label="Select download format",
        value="mp3"
    )


ui.run(host="0.0.0.0", port=8080)
