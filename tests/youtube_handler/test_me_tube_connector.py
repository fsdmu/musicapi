import json
from unittest.mock import patch, MagicMock

import pytest

from src.youtube_handler.me_tube_connector import MeTubeConnector


def dummy_download_url(single_url, quality, download_format, add_without_download):
    return f"Queued {single_url} with quality {quality} and format {download_format}"


def dummy_add_to_me_tube(single_url, quality, download_format):
    return f"Queued {single_url} with quality {quality} and format {download_format}"


@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_me_tube_connector_initialization(mock_db_connector):
    """Test that MeTubeConnector initializes correctly with a base URL."""
    base_url = "https://example.com/api"
    mt = MeTubeConnector(base_url=base_url)
    assert mt.base_url == base_url
    assert mt.db_connector == mock_db_connector.return_value


@patch("os.environ.get")
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_me_tube_connector_initialization_no_explicit_env_var(
    mock_db_connector, mock_get
):
    """Test that MeTubeConnector uses the environment variable if no URL is provided."""
    env_url = "https://env-example.com/api"
    mock_get.return_value = env_url

    mt = MeTubeConnector()
    assert mt.base_url == env_url


@patch("os.environ.get", return_value=None)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_me_tube_connector_initialization_no_url(mock_db_connector, mock_get):
    """Test that MeTubeConnector raises an error if no URL is provided."""
    with pytest.raises(ValueError):
        MeTubeConnector()


@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._download_url",
    side_effect=dummy_download_url,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_queue_download_single_url(mock_db_connector, mock_download_url):
    """Test queuing a single download URL."""
    url = "https://example.com/watch?v=video1"

    mt_connector = MeTubeConnector(base_url="https://example.com/api")
    response = mt_connector.queue_download(url, quality="High", download_format="mp4")

    assert response == [f"Queued {url} with quality High and format mp4"]


@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._download_url",
    side_effect=dummy_download_url,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_queue_download_multiple_urls(mock_db_connector, mock_download_url):
    """Test queuing multiple download URLs."""

    urls = [
        "https://example.com/watch?v=video1",
        "https://example.com/watch?v=video2",
        "https://example.com/watch?v=video3",
        None,
    ]

    mt = MeTubeConnector(base_url="https://example.com/api")
    responses = mt.queue_download(urls, quality="Medium", download_format="mp3")
    expected_responses = [
        f"Queued {url} with quality Medium and format mp3" for url in urls
    ]

    assert responses == expected_responses


@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._add_to_me_tube",
    side_effect=dummy_add_to_me_tube,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_download_url_single(mock_db_connector, mock_add_to_me_tube):
    """Test the _download_url method for a single URL."""
    mock_db_instance = MagicMock()
    mock_db_instance.get_song.return_value = None
    mock_db_connector.return_value = mock_db_instance

    url = "https://example.com/watch?v=video1"

    mt = MeTubeConnector(base_url="https://example.com/api")
    response = mt._download_url(
        url, quality="High", download_format="mp4", add_without_download=False
    )

    assert response == f"Queued {url} with quality High and format mp4"

    assert mock_db_instance.get_song.call_args[0][0] == url

    assert mock_db_instance.add_song.call_args[0][0] == url

    assert not mock_db_instance.get_album.called
    assert not mock_db_instance.add_album.called

    assert mock_add_to_me_tube.call_args[0][0] == url
    assert mock_add_to_me_tube.call_args[0][1] == "High"
    assert mock_add_to_me_tube.call_args[0][2] == "mp4"


@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._add_to_me_tube",
    side_effect=dummy_add_to_me_tube,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_download_url_single_existing_song(mock_db_connector, mock_add_to_me_tube):
    """Test the _download_url method for an existing song URL."""

    mock_db_instance = MagicMock()
    mock_db_instance.get_song.return_value = {
        "id": 1,
        "url": "https://example.com/watch?v=video1",
    }
    mock_db_connector.return_value = mock_db_instance

    url = "https://example.com/watch?v=video1"

    mt = MeTubeConnector(base_url="https://example.com/api")
    response = mt._download_url(
        url, quality="High", download_format="mp4", add_without_download=False
    )

    assert response is None

    assert mock_db_instance.get_song.call_args[0][0] == url

    assert not mock_db_instance.add_song.called
    assert not mock_db_instance.get_album.called
    assert not mock_db_instance.add_album.called

    assert not mock_add_to_me_tube.called


@patch(
    "src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher.get_album_songs",
)
@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._add_to_me_tube",
    side_effect=dummy_add_to_me_tube,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_download_url_playlist(
    mock_db_connector, mock_add_to_me_tube, mock_get_album_songs
):
    """Test the _download_url method for a playlist URL."""
    mock_db_instance = MagicMock()
    mock_db_instance.get_album.return_value = None
    mock_db_connector.return_value = mock_db_instance

    url = "https://example.com/playlist?list=playlist1"
    song_urls = [
        "https://example.com/watch?v=song1",
        "https://example.com/watch?v=song2",
        "https://example.com/watch?v=song3",
    ]
    mock_get_album_songs.return_value = song_urls

    mt = MeTubeConnector(base_url="https://example.com/api")
    response = mt._download_url(
        url, quality="High", download_format="mp4", add_without_download=False
    )

    for index, song_url in enumerate(song_urls):
        assert mock_db_instance.add_song.call_args_list[index][0][0] == song_url

    assert response == f"Queued {url} with quality High and format mp4"

    assert mock_add_to_me_tube.call_args[0][0] == url
    assert mock_add_to_me_tube.call_args[0][1] == "High"
    assert mock_add_to_me_tube.call_args[0][2] == "mp4"


@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._add_to_me_tube",
    side_effect=dummy_add_to_me_tube,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_download_url_playlist_existing_album(mock_db_connector, mock_add_to_me_tube):
    """Test the _download_url method for an existing playlist URL."""
    url = "https://example.com/playlist?list=playlist1"

    mock_db_instance = MagicMock()
    mock_db_instance.get_album.return_value = {
        "id": 1,
        "url": url,
    }
    mock_db_connector.return_value = mock_db_instance

    mt = MeTubeConnector(base_url="https://example.com/api")
    response = mt._download_url(
        url, quality="High", download_format="mp4", add_without_download=False
    )

    assert response is None

    assert mock_db_instance.get_album.call_args[0][0] == url

    assert not mock_db_instance.add_song.called
    assert not mock_db_instance.get_song.called
    assert not mock_db_instance.add_album.called

    assert not mock_add_to_me_tube.called


@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._add_to_me_tube",
    side_effect=dummy_add_to_me_tube,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_download_url_unsupported_format(mock_db_connector, mock_add_to_me_tube):
    """Test that _download_url raises ValueError for unsupported URL formats."""
    mt = MeTubeConnector(base_url="https://example.com/api")
    url = "https://example.com/unsupported_format"

    with pytest.raises(ValueError):
        mt._download_url(
            url, quality="High", download_format="mp4", add_without_download=False
        )

    assert not mock_add_to_me_tube.called


@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._add_to_me_tube",
    side_effect=dummy_add_to_me_tube,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_download_url_single_no_download(mock_db_connector, mock_add_to_me_tube):
    """Test the _download_url method for a single URL with add_without_download=True."""
    mock_db_instance = MagicMock()
    mock_db_instance.get_song.return_value = None
    mock_db_connector.return_value = mock_db_instance

    url = "https://example.com/watch?v=video1"

    mt = MeTubeConnector(base_url="https://example.com/api")
    response = mt._download_url(
        url, quality="High", download_format="mp4", add_without_download=True
    )

    assert response is None

    assert mock_db_instance.get_song.call_args[0][0] == url

    assert mock_db_instance.add_song.call_args[0][0] == url

    assert not mock_db_instance.get_album.called
    assert not mock_db_instance.add_album.called

    assert not mock_add_to_me_tube.called


@patch("src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher.get_album_songs")
@patch(
    "src.youtube_handler.me_tube_connector.MeTubeConnector._add_to_me_tube",
    side_effect=dummy_add_to_me_tube,
)
@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
def test_download_url_playlist_no_listequals(
    mock_db_connector, mock_add_to_me_tube, mock_get_album_songs
):
    """Test that _download_url raises ValueError for playlist URL without 'list='."""
    mock_db_instance = MagicMock()
    mock_db_instance.get_album.return_value = None
    mock_db_connector.return_value = mock_db_instance

    url = "https://example.com/playlist?playlist1"
    song_urls = [
        "https://example.com/watch?v=song1",
        "https://example.com/watch?v=song2",
        "https://example.com/watch?v=song3",
    ]
    mock_get_album_songs.return_value = song_urls

    mt = MeTubeConnector(base_url="https://example.com/api")
    with pytest.raises(ValueError):
        mt._download_url(
            url, quality="High", download_format="mp4", add_without_download=False
        )

    assert mock_db_instance.get_album.called
    assert not mock_db_instance.add_album.called
    assert not mock_db_instance.add_song.called

    assert mock_add_to_me_tube.call_args[0][0] == url
    assert mock_add_to_me_tube.call_args[0][1] == "High"
    assert mock_add_to_me_tube.call_args[0][2] == "mp4"


@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
@patch("src.youtube_handler.me_tube_connector.requests.post")
def test_add_to_me_tube(mock_post, mock_db_connector):
    """Test the _add_to_me_tube method."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    base_url = "https://example.com/api"

    url = "https://example.com/watch?v=video1"
    quality = "High"
    download_format = "mp4"

    mt = MeTubeConnector(base_url=base_url)
    response = mt._add_to_me_tube(url, quality, download_format)

    assert response == mock_response

    expected_data = json.dumps(
        {
            "url": url,
            "quality": quality,
            "format": download_format,
        }
    )

    mock_post.assert_called_once_with(
        f"{base_url}/add",
        data=expected_data,
        headers={"Content-Type": "application/json"},
    )


@patch("src.youtube_handler.me_tube_connector.DatabaseConnector")
@patch("src.youtube_handler.me_tube_connector.requests.post")
def test_add_to_me_tube_failure(mock_post, mock_db_connector):
    """Test that _add_to_me_tube handles non-200 responses."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    base_url = "https://example.com/api"

    url = "https://example.com/watch?v=video1"
    quality = "High"
    download_format = "mp4"

    mt = MeTubeConnector(base_url=base_url)
    response = mt._add_to_me_tube(url, quality, download_format)

    assert response is None

    expected_data = json.dumps(
        {
            "url": url,
            "quality": quality,
            "format": download_format,
        }
    )

    mock_post.assert_called_once_with(
        f"{base_url}/add",
        data=expected_data,
        headers={"Content-Type": "application/json"},
    )
