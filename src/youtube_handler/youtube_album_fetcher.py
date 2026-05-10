"""Module to fetch album and song information from YouTube Music."""

from typing import Any

from ytmusicapi import YTMusic

from src.logging.event_logger import log_event

ytmusic = YTMusic()


class YoutubeAlbumFetcher:
    """A class to fetch album and song information from YouTube Music."""

    @staticmethod
    @log_event("youtube.get_album_ids")
    def get_album_ids(artist_url: str, session_id: str | None = None) -> list[str]:
        """Fetch playlist URLs for ALL releases (albums, EPs, singles)."""
        artist_id = YoutubeAlbumFetcher._get_id_by_url(artist_url)
        artist_details = YoutubeAlbumFetcher._get_artist_details(
            artist_id, session_id=session_id
        )
        album_ids = YoutubeAlbumFetcher._get_all_release_ids(
            artist_details, session_id=session_id
        )
        return [YoutubeAlbumFetcher._get_album_url(aid) for aid in album_ids]

    @staticmethod
    def _get_id_by_url(url: str) -> str:
        if not url or "channel/" not in url:
            raise ValueError(f"Invalid YouTube Music channel URL: {url}")
        id_side = url.split("channel/")[1]
        return id_side.split("/")[0]

    @staticmethod
    def _get_album_url(playlist_id: str) -> str:
        if not playlist_id:
            raise ValueError("Playlist ID cannot be empty")
        return r"https://music.youtube.com/playlist?list=" + playlist_id

    @staticmethod
    @log_event("youtube._get_all_release_ids")
    def _get_all_release_ids(
        artist_details: dict, session_id: str | None = None
    ) -> list[str]:
        """Return audio playlist IDs for every release (album/EP/single).

        Uses the required `params` argument and handles pagination
        via the continuation token.
        """
        all_playlist_ids = []

        for section_key in ("albums", "singles"):
            section = artist_details.get(section_key, {})
            if not section:
                continue

            # The documentation explicitly says to use both `browseId` and `params`
            # from the artist details section. `params` is mandatory.
            browse_id = section.get("browseId")
            params = section.get("params")
            if not browse_id or not params:
                # Fallback: if params are missing, try the limited results
                for item in section.get("results", []):
                    album_browse_id = item.get("browseId")
                    if album_browse_id:
                        details = ytmusic.get_album(album_browse_id)
                        pid = details.get("audioPlaylistId")
                        if pid:
                            all_playlist_ids.append(pid)
                continue

            # Paginate correctly using the continuation token
            while True:
                # Correctly pass `params` (required) and `limit`
                response = ytmusic.get_artist_albums(
                    browse_id, params=params, limit=None
                )
                releases = response if isinstance(
                    response, list
                ) else response.get("results", [])
                for release in releases:
                    release_browse_id = release.get("browseId")
                    if not release_browse_id:
                        continue
                    album_details = ytmusic.get_album(release_browse_id)
                    playlist_id = album_details.get("audioPlaylistId")
                    if playlist_id:
                        all_playlist_ids.append(playlist_id)

                continuation = response.get("continuation") if isinstance(
                    response, dict
                ) else None
                if not continuation:
                    break
                params = continuation

        if not all_playlist_ids:
            raise ValueError("No releases found for this artist.")
        return all_playlist_ids

    @staticmethod
    @log_event("youtube._get_artist_details")
    def _get_artist_details(
        artist_id: str, session_id: str | None = None
    ) -> dict[str, Any]:
        return ytmusic.get_artist(artist_id)

    @staticmethod
    @log_event("youtube.get_album_songs")
    def get_album_songs(playlist_id: str, session_id: str | None = None) -> list[str]:
        playlist = ytmusic.get_playlist(playlist_id, limit=None)
        tracks = playlist.get("tracks", [])
        songs = []
        for track in tracks:
            video_id = track.get("videoId")
            if video_id:
                song_url = ("https://music.youtube.com/"
                            f"watch?v={video_id}&list={playlist_id}")
                songs.append(song_url)
        return songs
