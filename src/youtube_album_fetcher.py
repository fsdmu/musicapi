"""Module to fetch album and song information from YouTube Music."""
from typing import Dict, Any, List

from ytmusicapi import YTMusic

ytmusic = YTMusic()


class YoutubeAlbumFetcher:
    """A class to fetch album and song information from YouTube Music."""

    @staticmethod
    def get_album_ids(artist_url: str) -> List[str]:
        """Fetch album URLs for a given YouTube Music artist channel URL.

        Args:
            artist_url: The YouTube Music channel URL.

        Returns:
            A list of YouTube Music playlist URLs for the artist's albums.

        """
        artist_id = YoutubeAlbumFetcher._get_id_by_url(artist_url)
        artist_details = YoutubeAlbumFetcher._get_artist_details(artist_id)
        album_ids = YoutubeAlbumFetcher._get_albums(artist_details)
        return [YoutubeAlbumFetcher._get_album_url(id) for id in album_ids]

    @staticmethod
    def _get_id_by_url(url: str) -> str:
        """Extract the YouTube Music artist ID from a channel URL.

        Args:
            url: The YouTube Music channel URL.

        Returns:
            The YouTube Music artist ID.

        """
        id_side = url.split("channel/")[1]
        return id_side.split("/")[0]

    @staticmethod
    def _get_album_url(playlist_id: str) -> str:
        """Construct a YouTube Music playlist URL from a playlist ID.

        Args:
            playlist_id: The YouTube Music playlist ID.

        Returns:
            The full YouTube Music playlist URL.
        """
        return r"https://music.youtube.com/playlist?list=" + playlist_id

    @staticmethod
    def _get_albums(artist_details: dict, get_eps: bool = True) -> List[str]:
        """Extract album IDs from artist details.

        Args:
            artist_details: A dictionary containing artist details.
            get_eps: Whether to include EPs in the album list.

        Returns:
            A list of album IDs.

        Raises:
            ValueError: If no album details or IDs are found.

        """
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

        if get_eps:
            album_ids.extend(YoutubeAlbumFetcher.get_eps(artist_details))

        return album_ids

    @staticmethod
    def _get_artist_details(artist_id: str) -> Dict[str, Any]:
        """Fetch artist details from YouTube Music by artist ID.

        Args:
            artist_id: The YouTube Music artist ID.

        Returns:
            A dictionary containing artist details.
        """
        return ytmusic.get_artist(artist_id)

    @staticmethod
    def get_album_songs(playlist_id: str) -> List[str]:
        """Fetch song URLs from a YouTube Music playlist ID.

        Args:
            playlist_id: The YouTube Music playlist ID.

        Returns:
            A list of song URLs in the playlist.

        """
        playlist = ytmusic.get_playlist(playlist_id, limit=None)
        tracks = playlist.get("tracks", [])

        songs = []
        for track in tracks:
            video_id = track.get("videoId")
            if video_id:
                song_url = f"https://music.youtube.com/watch?v={video_id}&list={playlist_id}"
                songs.append(song_url)
        return songs

    @staticmethod
    def get_eps(artist_details: Dict) -> List[str]:
        """Fetch EPs for a given artist ID from YouTube Music.

        Args:
            artist_details: A dictionary containing artist details.

        Returns:
            A list of EP playlist IDs.

        """
        releases = artist_details.get("singles", {}).get("results", [])

        eps = []

        for item in releases:
            playlist_id = item.get("browseId")
            album_details = ytmusic.get_album(playlist_id)

            track_count = len(album_details.get("tracks", []))

            if track_count <= 1:
                continue
            eps.append(album_details.get('audioPlaylistId'))

        return eps
