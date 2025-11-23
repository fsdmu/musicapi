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
    url = sa.Column(sa.String)


class Albums(Base):
    __tablename__ = "albums"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String)
    artistId = sa.Column(sa.Integer, sa.ForeignKey(Artist.id))


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

    def get_albums(self, artist_id: int) -> List[str]:
        album_urls = []
        stmt = select(Albums).where(Albums.artistId == artist_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            for album in result.fetchall():
                album_urls.append(album.url)
        return album_urls

    def add_artist(self, artist_url: str) -> Row[Any]:
        stmt = insert(Artist).values(url=artist_url)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    def add_album(self, album_url: str, artist_id: int) -> Row[Any]:
        stmt = insert(Albums).values(url=album_url, artistId=artist_id)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).inserted_primary_key
            conn.commit()
            return res

    @staticmethod
    def _get_engine() -> Engine:
        user = os.environ['DB_USER']
        password = os.environ['DB_PASSWORD']
        url = os.environ['DB_URL']
        port = os.environ['DB_PORT']
        database = os.environ['DB_DATABASE']
        return sa.create_engine(
            f"mysql+mysqlconnector://{user}:{password}@{url}:{port}/{database}")
