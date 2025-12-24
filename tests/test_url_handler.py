import pytest

from src.url_handler import UrlHandler


def test_get_handler_returns_youtube_handler(monkeypatch):
    """Ensure youtube URLs return a YoutubeDownloadHandler instance."""

    class DummyHandler:
        def __init__(self, db_connector):
            self.db = db_connector

    dummy_db = object()
    monkeypatch.setattr("src.url_handler.DatabaseConnector", lambda: dummy_db)
    monkeypatch.setattr("src.url_handler.YoutubeDownloadHandler", DummyHandler)

    handler = UrlHandler.get_handler("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert isinstance(handler, DummyHandler)
    assert handler.db is dummy_db


def test_get_handler_unsupported_url(monkeypatch):
    """Unsupported URLs should raise a ValueError."""
    monkeypatch.setattr("src.url_handler.DatabaseConnector", lambda: object())
    monkeypatch.setattr("src.url_handler.YoutubeDownloadHandler", object)

    with pytest.raises(ValueError):
        UrlHandler.get_handler("https://example.com/track/1")
