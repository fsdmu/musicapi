"""Database connector for managing the database."""

import os
from typing import List, Optional, Any

import sqlalchemy as sa
from sqlalchemy import insert, Engine, select, Row, Column
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for declarative models."""

    pass


class Artist(Base):
    """SQLAlchemy model for the 'artist' table."""

    __tablename__ = "artist"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String, unique=True)
    auto_download = sa.Column(sa.Boolean, default=False)


class Albums(Base):
    """SQLAlchemy model for the 'albums' table."""

    __tablename__ = "albums"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String, unique=True)


class Songs(Base):
    """SQLAlchemy model for the 'songs' table."""

    __tablename__ = "songs"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String, unique=True)


class DatabaseConnector:
    """Database connector for managing artists, albums, and songs."""

    def __init__(self) -> None:
        """Initialize the DatabaseConnector and set up the database engine."""
        self.artist_table = "artist"
        self.albums_table = "albums"

        self.engine = self._get_engine()

    def remove_album(self, album_url: str) -> None:
        """Remove an album from the database.

        Args:
            album_url: The URL of the album to remove.

        """
        stmt = sa.delete(Albums).where(Albums.url == album_url)
        with self.engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def get_artist_id(self, artist_url: str) -> Optional[int]:
        """Get the artist ID for a given artist URL.

        Args:
            artist_url: The URL of the artist.

        Returns:
            The artist ID if found, otherwise None.

        """
        stmt = select(Artist.id).where(Artist.url == artist_url)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return result[0] if result else None

    def add_artist(self, artist_url: str, auto_download: bool) -> Optional[Row[Any]]:
        """Add an artist to the database if not already present.

        Args:
            artist_url: The URL of the artist.
            auto_download: Whether to mark the artist for auto-download.

        Returns:
            The artist ID.

        """
        artist = self.get_artist(artist_url)
        if artist is not None:
            if auto_download and not artist.auto_download:
                self._add_auto_download_existing_artist(artist[0])
            return artist
        stmt = insert(Artist).values(url=artist_url, auto_download=auto_download)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_album(self, album_url: str) -> Optional[Row[Any]]:
        """Add an album to the database if not already present.

        Args:
            album_url: The URL of the album.

        Returns:
            The album ID.

        """
        album = self.get_album(album_url)
        if album is not None:
            return album
        stmt = insert(Albums).values(url=album_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res[0]

    def add_song(self, song_url: str) -> Optional[Row[Any]]:
        """Add a song to the database if not already present.

        Args:
            song_url: The URL of the song.

        Returns:
            The song ID.

        """
        song = self.get_song(song_url)
        if song is not None:
            return song
        stmt = insert(Songs).values(url=song_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res[0]

    def _add_auto_download_existing_artist(self, artist_id: int) -> Any:
        """Mark an artist for auto-download in the database.

        Args:
            artist_id: The id of the artist.

        Returns:
            The artist ID.

        """
        with self.engine.connect() as conn:
            update_stmt = (
                sa.update(Artist)
                .where(Artist.id == artist_id)
                .values(auto_download=True)
            )
            res = conn.execute(update_stmt)
            conn.commit()
            return res

    def get_auto_download_artists(self) -> List[str]:
        """Retrieve a list of artist URLs marked for auto-download.

        Returns:
            A list of artist URLs.

        """
        artist_urls = []
        stmt = select(Artist).where(Artist.auto_download == True)  # noqa: E712
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            for artist in result.fetchall():
                artist_urls.append(artist.url)
        return artist_urls

    def get_song(self, song_url) -> Optional[Row[Any]]:
        """Get the song ID for a given song URL.

        Args:
            song_url: The URL of the song.

        Returns:
            The song ID if found, otherwise None.

        """
        stmt = select(Songs.id).where(Songs.url == song_url)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()

            if not result:
                if "music.youtube.com" in song_url:
                    alt_url = song_url.replace("music.youtube.com", "youtube.com")
                    stmt = select(Songs.id).where(Songs.url == alt_url)
                    result = conn.execute(stmt).fetchone()
                elif "youtube.com" in song_url:
                    alt_url = song_url.replace("youtube.com", "music.youtube.com")
                    stmt = select(Songs.id).where(Songs.url == alt_url)
                    result = conn.execute(stmt).fetchone()
                else:
                    return None

            return result[0] if result else None

    def get_album(self, album_url) -> Optional[Row[Any]]:
        """Get the album ID for a given album URL.

        Args:
            album_url: The URL of the album.

        Returns:
            The album ID if found, otherwise None.

        """
        stmt = select(Albums.id).where(Albums.url == album_url)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return result[0] if result else None

    def get_artist(self, artist_url: str) -> Optional[Row[Any]]:
        """Get the artist ID for a given artist URL.

        Args:
            artist_url: The URL of the artist.

        Returns:
            The artist ID if found, otherwise None.

        """
        stmt = select(Artist).where(Artist.url == artist_url)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return result if result else None

    @staticmethod
    def _get_engine() -> Engine:
        """Create and return a SQLAlchemy engine using environment variables.

        Returns:
            A SQLAlchemy Engine instance.

        """
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        url = os.environ["DB_URL"]
        port = os.environ["DB_PORT"]
        database = os.environ["DB_DATABASE"]
        return sa.create_engine(
            f"mysql+mysqlconnector://{user}:{password}@{url}:{port}/{database}"
        )
