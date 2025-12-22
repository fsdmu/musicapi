import os
from typing import List, Optional, Any

import sqlalchemy as sa
from sqlalchemy import insert, Engine, select, Row
from sqlalchemy.orm import DeclarativeBase

from src.youtube_album_fetcher import YoutubeAlbumFetcher


class Base(DeclarativeBase):
    pass


class Artist(Base):
    __tablename__ = "artist"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String, unique=True)
    auto_download = sa.Column(sa.Boolean, default=False)


class Albums(Base):
    __tablename__ = "albums"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String, unique=True)

class Songs(Base):
    __tablename__ = "songs"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String, unique=True)


class DatabaseConnector:
    def __init__(self):
        self.artist_table = "artist"
        self.albums_table = "albums"

        self.engine = self._get_engine()

    def get_artist_id(self, artist_url: str) -> Optional[int]:
        stmt = select(Artist.id).where(Artist.url == artist_url)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return result[0] if result else None

    def add_artist(self, artist_url: str) -> Row[Any]:
        artist = self.get_artist(artist_url)
        if artist is not None:
            return artist
        stmt = insert(Artist).values(url=artist_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_album(self, album_url: str) -> Row[Any]:
        album = self.get_album(album_url)
        if album is not None:
            return album
        stmt = insert(Albums).values(url=album_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_song(self, song_url: str) -> Row[Any]:
        song = self.get_song(song_url)
        if song is not None:
            return song
        stmt = insert(Songs).values(url=song_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_auto_download_artist(self, artist_url: str) -> Optional[int]:
        existing_artist_id = self.get_artist_id(artist_url)
        with self.engine.connect() as conn:
            if existing_artist_id is not None:
                stmt = (
                    sa.update(Artist)
                    .where(Artist.id == existing_artist_id)
                    .values(auto_download=True)
                )
                conn.execute(stmt)
                conn.commit()
                return existing_artist_id
            else:
                stmt = insert(Artist).values(
                    url=artist_url,
                    auto_download=True
                )
                result = conn.execute(stmt)
                conn.commit()
                return result.inserted_primary_key[0]

    def get_auto_download_artists(self) -> List[str]:
        artist_urls = []
        stmt = select(Artist).where(Artist.auto_download == True)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            for artist in result.fetchall():
                artist_urls.append(artist.url)
        return artist_urls

    def get_song(self, song_url) -> Optional[Row[Any]]:
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

    def get_album(self, album_url) -> Row[Any]:
        stmt = select(Albums.id).where(Albums.url == album_url)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return result[0] if result else None

    def get_artist(self, artist_url) -> Row[Any]:
        stmt = select(Artist.id).where(Artist.url == artist_url)
        with self.engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
            return result[0] if result else None

    @staticmethod
    def _get_engine() -> Engine:
        user = os.environ['DB_USER']
        password = os.environ['DB_PASSWORD']
        url = os.environ['DB_URL']
        port = os.environ['DB_PORT']
        database = os.environ['DB_DATABASE']
        return sa.create_engine(
            f"mysql+mysqlconnector://{user}:{password}@{url}:{port}/{database}")
