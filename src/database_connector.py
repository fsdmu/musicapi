import os
from typing import List, Optional, Any

import sqlalchemy as sa
from sqlalchemy import insert, Engine, select, Row
from sqlalchemy.orm import DeclarativeBase


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
            result = conn.execute(stmt)
            return result.fetchone()[0]

    def add_artist(self, artist_url: str) -> Row[Any]:
        stmt = insert(Artist).values(url=artist_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_album(self, album_url: str) -> Row[Any]:
        stmt = insert(Albums).values(url=album_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_song(self, song_url: str) -> Row[Any]:
        stmt = insert(Songs).values(url=song_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_auto_download_artist(self, artist_url: str) -> Row[Any]:
        existing_artist_id = self.get_artist_id(artist_url)
        if existing_artist_id is not None:
            stmt = sa.update(Artist).where(
                Artist.id == existing_artist_id).values(auto_download=True)
        else:
            stmt = insert(Artist).values(url=artist_url, auto_download=True)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def get_auto_download_artists(self) -> List[str]:
        artist_urls = []
        stmt = select(Artist).where(Artist.auto_download == True)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            for artist in result.fetchall():
                artist_urls.append(artist.url)
        return artist_urls

    @staticmethod
    def _get_engine() -> Engine:
        user = os.environ['DB_USER']
        password = os.environ['DB_PASSWORD']
        url = os.environ['DB_URL']
        port = os.environ['DB_PORT']
        database = os.environ['DB_DATABASE']
        return sa.create_engine(
            f"mysql+mysqlconnector://{user}:{password}@{url}:{port}/{database}")
