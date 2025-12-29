import pytest
import sqlalchemy as sa
from unittest.mock import patch, MagicMock

from src.database_connector import DatabaseConnector, Base


@pytest.fixture
def db():
    mock_env = {
        "DB_USER": "test",
        "DB_PASSWORD": "test",
        "DB_URL": "localhost",
        "DB_PORT": "3306",
        "DB_DATABASE": "test",
    }

    with patch.dict("os.environ", mock_env):
        with patch.object(DatabaseConnector, "_get_engine") as mocked_engine:
            engine = sa.create_engine("sqlite:///:memory:")
            mocked_engine.return_value = engine

            connector = DatabaseConnector()

            Base.metadata.create_all(engine)

            yield connector

    engine.dispose()


@pytest.mark.parametrize("auto_download", [True, False])
def test_add_and_get_artist(db, auto_download):
    url = "https://example.com/artist/1"
    db.add_artist(url, auto_download=auto_download)

    artist = db.get_artist(url)
    assert artist.id == 1
    assert artist.url == "https://example.com/artist/1"
    assert artist.auto_download == auto_download

    assert (url in db.get_auto_download_artists()) == auto_download


def test_add_and_get_artist_id(db):
    url = "https://example.com/artist/1"
    db.add_artist(url, auto_download=True)

    artist_id = db.get_artist_id(url)
    assert artist_id == 1
    assert url in db.get_auto_download_artists()


def test_song_yt_url_mapping_logic(db):
    yt_url = "https://youtube.com/watch?v=abc"
    db.add_song(yt_url)

    result = db.get_song("https://music.youtube.com/watch?v=abc")
    assert result is not None


def test_add_album_idempotency(db):
    url = "https://example.com/album/99"
    id1 = db.add_album(url)
    id2 = db.add_album(url)

    assert id1 == id2


def test_add_get_album(db):
    url = "https://example.com/album/99"
    id = db.add_album(url)

    assert db.get_album(url) == id


def test_add_existing_album(db):
    url = "https://example.com/album/99"
    id_new = db.add_album(url)
    id_existing = db.add_album(url)

    assert db.get_album(url) == id_new
    assert id_new == id_existing


def test_remove_album(db):
    url = "https://example.com/album/99"
    db.add_album(url)
    db.remove_album(url)

    assert db.get_album(url) is None


def test_remove_album_no_album(db):
    url = "https://example.com/album/99"
    db.remove_album(url)
    assert db.get_album(url) is None


@pytest.mark.parametrize(
    "initial_auto_download,update_auto_download,expected_auto_download",
    [
        (True, True, True),
        (True, False, True),
        (False, True, True),
        (False, False, False),
    ],
)
def test_add_artist_existing(
    db, initial_auto_download, update_auto_download, expected_auto_download
):
    url = "https://example.com/artist/99"
    db.add_artist(url, auto_download=initial_auto_download)
    db.add_artist(url, auto_download=update_auto_download)

    artist = db.get_artist(url)
    assert artist is not None
    assert artist.auto_download == expected_auto_download


def test_add_song(db):
    url1 = "https://example.com/song/1"
    url2 = "https://example.com/song/2"

    id = db.add_song(url1)
    assert id is not None
    assert db.get_song(url1) == id

    assert db.add_song(url1) == id
    assert db.get_song(url2) is None


@pytest.mark.parametrize("driver", [None, "postgres"])
@patch("sqlalchemy.create_engine")
def test_get_engine(mock_create_engine, driver):
    user, pw, url, port, db = "User1", "Pass1", "Url1", "Port1", "Db1"
    driver = driver if driver else "mysql+mysqlconnector"
    mock_env = {
        "DB_USER": user,
        "DB_PASSWORD": pw,
        "DB_URL": url,
        "DB_PORT": port,
        "DB_DATABASE": db,
        "DB_DRIVER": driver,
    }

    mock_engine_instance = MagicMock()
    mock_create_engine.return_value = mock_engine_instance

    with patch.dict("os.environ", mock_env):
        result = DatabaseConnector._get_engine()

    assert result == mock_engine_instance

    expected_conn_str = f"{driver}://{user}:{pw}@{url}:{port}/{db}"
    mock_create_engine.assert_called_once_with(expected_conn_str)
