import pytest

from src.youtube_handler.youtube_download_handler import YoutubeDownloadHandler


def _stub_handler(monkeypatch):
    class DummyMt:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr("src.youtube_handler.youtube_download_handler.MeTubeConnector", DummyMt)
    monkeypatch.setattr("src.youtube_handler.youtube_download_handler.DatabaseConnector", lambda: None)


def test_get_warning_discourages_plain_youtube(monkeypatch):
    _stub_handler(monkeypatch)
    handler = YoutubeDownloadHandler(db_connector=None)  # type: ignore[arg-type]

    warning = handler.get_warning("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert "youtube.com links" in warning


def test_get_warning_allows_music_domain(monkeypatch):
    _stub_handler(monkeypatch)
    handler = YoutubeDownloadHandler(db_connector=None)  # type: ignore[arg-type]

    warning = handler.get_warning("https://music.youtube.com/watch?v=dQw4w9WgXcQ")
    assert warning is None
