from typing import Dict, Any, List

from ytmusicapi import YTMusic

ytmusic = YTMusic()


class YoutubeAlbumFetcher:
    @staticmethod
    def get_album_ids(artist_url: str) -> List[str]:
        artist_id = YoutubeAlbumFetcher._get_id_by_url(artist_url)
        artist_details = YoutubeAlbumFetcher._get_artist_details(artist_id)
        album_ids = YoutubeAlbumFetcher._get_albums(artist_details)
        return [YoutubeAlbumFetcher._get_album_url(id) for id in album_ids]

    @staticmethod
    def _get_id_by_url(url: str) -> str:
        id_side = url.split("channel/")[1]
        return id_side.split("/")[0]

    @staticmethod
    def _get_album_url(playlist_id: str) -> str:
        return r"https://music.youtube.com/playlist?list=" + playlist_id

    @staticmethod
    def _get_albums(artist_details: dict) -> List[str]:
        album_ids = []

        album_dict = artist_details.get("albums", {})
        if not album_dict:
            raise ValueError("No album details found")
        albums = album_dict.get("results", [])

        if not albums:
            raise ValueError("No album details found")

        for album in albums:
            id = album.get("audioPlaylistId")
            if not id:
                raise ValueError(f"No album id found for: {album}")
            album_ids.append(id)
        return album_ids

    @staticmethod
    def _get_artist_details(artist_id: str) -> Dict[str, Any]:
        return ytmusic.get_artist(artist_id)