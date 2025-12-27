from unittest.mock import patch

import pytest

from src.youtube_handler.youtube_download_handler import YoutubeDownloadHandler


@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
def test_youtube_download_handler_init(mock_me_tube_connector, mock_db_connector):
    """Test initialization of YoutubeDownloadHandler."""
    handler = YoutubeDownloadHandler(db_connector=mock_db_connector)

    assert handler.db_connector == mock_db_connector
    assert handler.mt_connector == mock_me_tube_connector()


@pytest.mark.parametrize("quality,download_format", [("Best", "mp3"), ("High", "mp4")])
@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
@patch(
    "src.youtube_handler.youtube_download_handler."
    "YoutubeDownloadHandler._handle_channel_url"
)
def test_download_channel_url(
    mock_handle_channel_url,
    mock_me_tube_connector,
    mock_db_connector,
    quality,
    download_format,
):
    """Test downloading from a channel URL."""
    handler = YoutubeDownloadHandler(db_connector=mock_db_connector)
    url = "https://www.youtube.com/channel/CHANNEL_ID"

    handler.download(
        url,
        auto_download=True,
        quality=quality,
        download_format=download_format,
    )

    mock_handle_channel_url.assert_called_once_with(
        url,
        True,
        quality=quality,
        download_format=download_format,
    )
    assert not mock_me_tube_connector().queue_download.called


@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
@patch(
    "src.youtube_handler.youtube_download_handler."
    "YoutubeDownloadHandler._handle_channel_url"
)
def test_download_playlist_url(
    mock_handle_channel_url,
    mock_me_tube_connector,
    mock_db_connector,
):
    """Test downloading from a playlist URL."""
    handler = YoutubeDownloadHandler(db_connector=mock_db_connector)
    url = "https://www.youtube.com/playlist?list=PLAYLIST_ID"

    handler.download(url, download_format="flac", quality="High")

    mock_me_tube_connector().queue_download.assert_called_once_with(
        url,
        quality="High",
        download_format="flac",
        add_without_download=False,
    )
    assert not mock_handle_channel_url.called


@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
@patch(
    "src.youtube_handler.youtube_download_handler."
    "YoutubeDownloadHandler._handle_channel_url"
)
def test_download_unsupported_url(
    mock_handle_channel_url,
    mock_me_tube_connector,
    mock_db_connector,
):
    """Test downloading from an unsupported URL format."""
    handler = YoutubeDownloadHandler(db_connector=mock_db_connector)
    url = "https://www.youtube.com/unsupported_format"

    with pytest.raises(ValueError):
        handler.download(url)

    assert not mock_handle_channel_url.called
    assert not mock_me_tube_connector().queue_download.called


@pytest.mark.parametrize("auto_download", [True, False])
@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
@patch("src.youtube_handler.youtube_download_handler.YoutubeAlbumFetcher")
def test_handle_channel_url(
    mock_youtube_album_fetcher,
    mock_me_tube_connector,
    mock_db_connector,
    auto_download,
):
    """Test handling a channel URL."""
    album_id = "ALBUM_ID_1"
    album_url = f"https://example.com/playlist?list={album_id}"
    url = "https://www.example.com/channel/CHANNEL_ID"
    album_urls = [album_url]
    quality = "High"
    download_format = "mp4"
    song_url = "https://example.com/song1"
    album_songs = [song_url]

    mock_youtube_album_fetcher.get_album_ids.return_value = album_urls
    mock_youtube_album_fetcher.get_album_songs.return_value = album_songs

    handler = YoutubeDownloadHandler(db_connector=mock_db_connector)
    handler._handle_channel_url(
        url,
        auto_download=auto_download,
        quality=quality,
        download_format=download_format,
    )

    mock_youtube_album_fetcher.get_album_ids.assert_called_once_with(url)

    mock_db_connector.add_artist.assert_called_once_with(
        url,
        auto_download=auto_download,
    )

    mock_me_tube_connector().queue_download.assert_called_once_with(
        album_url,
        quality=quality,
        download_format=download_format,
        add_without_download=False,
    )

    mock_db_connector.add_album.assert_called_once_with(album_url)

    mock_youtube_album_fetcher.get_album_songs.assert_called_once_with(album_id)
    mock_db_connector.add_song.assert_called_once_with(song_url)


@pytest.mark.parametrize("auto_download", [True, False])
@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
@patch("src.youtube_handler.youtube_download_handler.YoutubeAlbumFetcher")
def test_handle_channel_url_download_error(
    mock_youtube_album_fetcher,
    mock_me_tube_connector,
    mock_db_connector,
    auto_download,
):
    """Test handling of a channel URL with an occurring download exception."""
    album_id = "ALBUM_ID_1"
    album_url = f"https://example.com/playlist?list={album_id}"
    url = "https://www.example.com/channel/CHANNEL_ID"
    album_urls = [album_url]
    quality = "High"
    download_format = "mp4"

    mock_youtube_album_fetcher.get_album_ids.return_value = album_urls
    mock_me_tube_connector().queue_download.side_effect = ValueError

    with pytest.raises(RuntimeError):
        handler = YoutubeDownloadHandler(db_connector=mock_db_connector)
        handler._handle_channel_url(
            url,
            auto_download=auto_download,
            quality=quality,
            download_format=download_format,
        )

    mock_youtube_album_fetcher.get_album_ids.assert_called_once_with(url)
    mock_db_connector.add_artist.assert_called_once_with(
        url,
        auto_download=auto_download,
    )

    assert not mock_db_connector.add_album.called
    assert not mock_db_connector.add_song.called


@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
def test_get_warning(mock_me_tube_connector, mock_db_connector):
    url = "youtube.com/watch"
    handler = YoutubeDownloadHandler(db_connector=mock_db_connector)

    result = handler.get_warning(url)

    assert "music.youtube.com" in result


@patch("src.youtube_handler.youtube_download_handler.DatabaseConnector")
@patch("src.youtube_handler.youtube_download_handler.MeTubeConnector")
def test_get_warning_no_warning(mock_me_tube_connector, mock_db_connector):
    url = "music.youtube.com/watch"
    handler = YoutubeDownloadHandler(db_connector=mock_db_connector)

    result = handler.get_warning(url)

    assert result is None
