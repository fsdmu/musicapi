from unittest.mock import patch

import pytest

from src.youtube_handler.youtube_album_fetcher import YoutubeAlbumFetcher


@patch("src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher._get_id_by_url")
@patch(
    "src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher._get_artist_details"
)
@patch("src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher._get_albums")
@patch(
    "src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher._get_album_url",
    side_effect=lambda url: url,
)
def test_get_album_ids(
    mock_get_album_url,
    mock_get_albums,
    mock_get_artist_details,
    mock_get_id_by_url,
):
    """Test fetching album IDs from a YouTube Music artist channel URL."""
    artist_url = "https://music.youtube.com/channel/UC1234567890"
    artist_id = "UC1234567890"
    artist_details = {"some": "details"}
    album_ids = ["ALBUM_ID_1", "ALBUM_ID_2"]
    album_urls = [
        "https://music.youtube.com/playlist?list=ALBUM_ID_1",
        "https://music.youtube.com/playlist?list=ALBUM_ID_2",
    ]

    mock_get_id_by_url.return_value = artist_id
    mock_get_artist_details.return_value = artist_details
    mock_get_albums.return_value = album_ids
    mock_get_album_url.side_effect = album_urls

    result = YoutubeAlbumFetcher.get_album_ids(artist_url)

    assert result == album_urls
    mock_get_id_by_url.assert_called_once_with(artist_url)
    mock_get_artist_details.assert_called_once_with(artist_id)
    mock_get_albums.assert_called_once_with(artist_details)
    assert mock_get_album_url.call_count == len(album_ids)


def test_get_id_by_url():
    """Test extracting the YouTube Music artist ID from a channel URL."""
    url = "https://example.com/channel/UC1234567890/some/path"
    expected_id = "UC1234567890"

    result = YoutubeAlbumFetcher._get_id_by_url(url)

    assert result == expected_id


def test_get_id_by_url_invalid():
    """Test that an invalid URL raises a ValueError."""
    invalid_url = "https://example.com/user/SomeUser"

    with pytest.raises(ValueError):
        YoutubeAlbumFetcher._get_id_by_url(invalid_url)


def test_get_album_url():
    """Test constructing a YouTube Music playlist URL from a playlist ID."""
    playlist_id = "ALBUM_ID_123"
    expected_url = f"https://music.youtube.com/playlist?list={playlist_id}"

    result = YoutubeAlbumFetcher._get_album_url(playlist_id)

    assert result == expected_url


def test_get_album_url_empty():
    """Test that an empty playlist ID raises a ValueError."""
    with pytest.raises(ValueError):
        YoutubeAlbumFetcher._get_album_url("")


@patch("src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher.get_eps")
def test_get_albums(mock_get_eps):
    """Test extracting album IDs from artist details."""
    artist_details = {
        "albums": {
            "results": [
                {"audioPlaylistId": "ALBUM_ID_1"},
                {"audioPlaylistId": "ALBUM_ID_2"},
            ],
        },
    }
    expected_album_ids = ["ALBUM_ID_1", "ALBUM_ID_2", "EP_ID_1"]

    mock_get_eps.return_value = [
        "EP_ID_1",
    ]

    result = YoutubeAlbumFetcher._get_albums(artist_details, get_eps=True)

    assert result == expected_album_ids
    mock_get_eps.assert_called_once_with(artist_details)


@patch("src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher.get_eps")
def test_get_albums_no_eps_found(mock_get_eps):
    """Test extracting album IDs from artist details without EPs."""
    artist_details = {
        "albums": {
            "results": [
                {"audioPlaylistId": "ALBUM_ID_1"},
                {"audioPlaylistId": "ALBUM_ID_2"},
            ],
        },
    }
    expected_album_ids = ["ALBUM_ID_1", "ALBUM_ID_2"]

    mock_get_eps.return_value = []

    result = YoutubeAlbumFetcher._get_albums(artist_details, get_eps=True)

    assert result == expected_album_ids
    mock_get_eps.assert_called_once_with(artist_details)


@patch("src.youtube_handler.youtube_album_fetcher.YoutubeAlbumFetcher.get_eps")
def test_get_albums_no_eps(mock_get_eps):
    """Test extracting album IDs from artist details without EPs."""
    artist_details = {
        "albums": {
            "results": [
                {"audioPlaylistId": "ALBUM_ID_1"},
                {"audioPlaylistId": "ALBUM_ID_2"},
            ],
        },
    }
    expected_album_ids = ["ALBUM_ID_1", "ALBUM_ID_2"]

    result = YoutubeAlbumFetcher._get_albums(artist_details, get_eps=False)

    assert result == expected_album_ids
    mock_get_eps.assert_not_called()


def test_get_albums_no_album_details():
    """Test that missing album details raise a ValueError."""
    artist_details = {}

    with pytest.raises(ValueError) as error:
        YoutubeAlbumFetcher._get_albums(artist_details)
        assert "No album details found" in str(error.value)


def test_get_albums_no_albums():
    """Test that empty album results raise a ValueError."""
    artist_details = {
        "albums": {
            "results": [],
        },
    }

    with pytest.raises(ValueError) as error:
        YoutubeAlbumFetcher._get_albums(artist_details)
        assert "No album details found" in str(error.value)


def test_get_albums_missing_audio_playlist_id():
    """Test that missing audioPlaylistId in album raises a ValueError."""
    artist_details = {
        "albums": {
            "results": [
                {"someOtherKey": "value"},
            ],
        },
    }

    with pytest.raises(ValueError) as error:
        YoutubeAlbumFetcher._get_albums(artist_details)
        assert "No album details found" in str(error.value)


@patch("src.youtube_handler.youtube_album_fetcher.ytmusic")
def test_get_artist_details(mock_ytmusic):
    """Test fetching artist details from YouTube Music by artist ID."""
    artist_id = "UC1234567890"
    expected_details = {"name": "Test Artist"}

    mock_ytmusic.get_artist.return_value = expected_details

    result = YoutubeAlbumFetcher._get_artist_details(artist_id)

    assert result == expected_details
    mock_ytmusic.get_artist.assert_called_once_with(artist_id)


@patch("src.youtube_handler.youtube_album_fetcher.ytmusic")
def test_get_album_songs(mock_ytmusic):
    """Test fetching song URLs from a YouTube Music playlist ID."""
    playlist_id = "ALBUM_ID_123"
    expected_songs = [
        "https://music.youtube.com/watch?v=SONG_ID_1&list=ALBUM_ID_123",
        "https://music.youtube.com/watch?v=SONG_ID_2&list=ALBUM_ID_123",
    ]

    mock_ytmusic.get_playlist.return_value = {
        "tracks": [
            {"videoId": "SONG_ID_1"},
            {"videoId": "SONG_ID_2"},
        ],
    }

    result = YoutubeAlbumFetcher.get_album_songs(playlist_id)

    assert result == expected_songs
    mock_ytmusic.get_playlist.assert_called_once_with(playlist_id, limit=None)


@patch("src.youtube_handler.youtube_album_fetcher.ytmusic")
def test_get_eps(mock_ytmusic):
    """Test fetching EP IDs from artist details."""

    def _mock_get_album(playlist_id):
        album_details = {
            "EP_ID_1": {
                "tracks": [
                    "Track 1",
                    "Track 2",
                ],
                "audioPlaylistId": "EP_ID_1",
            },
            "EP_ID_2": {
                "tracks": [],
                "audioPlaylistId": "EP_ID_2",
            },
        }
        return album_details.get(playlist_id)

    mock_ytmusic.get_album.side_effect = _mock_get_album

    artist_details = {
        "singles": {
            "results": [
                {"browseId": "EP_ID_1"},
                {"browseId": "EP_ID_2"},
                {"otherId": "NOT_AN_EP"},
            ]
        },
    }

    expected_eps = ["EP_ID_1"]

    mock_ytmusic.get_album.return_value = artist_details

    result = YoutubeAlbumFetcher.get_eps(artist_details)

    assert result == expected_eps
    mock_ytmusic.get_album.assert_any_call("EP_ID_1")
    mock_ytmusic.get_album.assert_any_call("EP_ID_2")
