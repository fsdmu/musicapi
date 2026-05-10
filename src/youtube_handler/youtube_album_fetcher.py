"""Module to fetch album and song information from YouTube Music."""

from typing import Any

from ytmusicapi import YTMusic

from src.logging.event_logger import log_event

ytmusic = YTMusic()


class YoutubeAlbumFetcher:
    """A class to fetch album and song information from YouTube Music."""

    @staticmethod
    def _collect_section_results(section: dict[str, Any]) -> list[dict[str, Any]]:
        """Collect all items from a section, following continuation tokens when present.

        This handles several shapes returned by ytmusicapi: initial 'results' and
        various continuation token structures. For each continuation token it calls
        ytmusic.get_continuation(...) and extracts list-like results.
        """
        items: list[dict[str, Any]] = []
        if not section:
            return items

        # initial results
        items.extend(
            section.get(
                "results", []
            ) if isinstance(section.get("results", []), list) else []
        )

        continuations = section.get("continuations", []) or []
        if not continuations:
            cont_token = None
            for key in ("continuation", "nextContinuationData"):
                if key in section:
                    value = section.get(key)
                    if isinstance(value, str):
                        cont_token = value
                    elif isinstance(value, dict):
                        cont_token = value.get("continuation") or value.get("token")
                    if cont_token:
                        continuations = [{"continuation": cont_token}]
                        break

        for cont in continuations:
            token = cont.get(
                "continuation"
            ) or cont.get("token") or cont.get(
                "nextContinuationData", {}
            ).get("continuation")
            if not token:
                continue
            try:
                next_page = ytmusic.get_continuation(token)
            except Exception:
                break

            if isinstance(next_page, dict):
                if "results" in next_page and isinstance(
                        next_page.get("results"), list
                ):
                    items.extend(next_page.get("results", []))
                    continue

                # nested containers
                for container_key in (
                        "albums", "singles", "continuationContents", "contents"
                ):
                    container = next_page.get(container_key)
                    if isinstance(container, dict) and isinstance(
                            container.get("results"
                                          ), list):
                        items.extend(container.get("results", []))
                        break
                    if isinstance(container, list):
                        items.extend(container)
                        break
                else:
                    # fallback: take first list value we find
                    for v in next_page.values():
                        if isinstance(v, list):
                            items.extend(v)
                            break
        return items

    @staticmethod
    @log_event("youtube.get_album_ids")
    def get_album_ids(artist_url: str,
                      get_songs: bool = False,
                      session_id: str | None = None) -> list[str]:
        """Fetch album URLs from a YouTube Music artist channel URL.

        Args:
            artist_url: The YouTube Music channel URL of the artist.
            get_songs: Whether to include songs that are not part of an album or EP.
            session_id: Optional session ID for logging.

        Returns:
            A list of YouTube Music playlist URLs for the artist's albums and
                optionally EPs/s that are not part of albums, depending on get_songs.

        """
        artist_id = YoutubeAlbumFetcher._get_id_by_url(artist_url)
        artist_details = YoutubeAlbumFetcher._get_artist_details(
            artist_id, session_id=session_id
        )
        album_ids = YoutubeAlbumFetcher._get_albums(
            artist_details,
            channel_id=artist_id,
            get_songs=get_songs,
            session_id=session_id,
        )
        return [YoutubeAlbumFetcher._get_album_url(aid) for aid in album_ids]

    @staticmethod
    def _get_id_by_url(url: str) -> str:
        """Extract the YouTube channel ID from a given YouTube Music channel URL.

        Args:
            url: The YouTube Music channel URL.

        Returns:
            The extracted YouTube channel ID.

        """
        if not url or "channel/" not in url:
            raise ValueError(f"Invalid YouTube Music channel URL: {url}")
        id_side = url.split("channel/")[1]
        return id_side.split("/")[0]

    @staticmethod
    def _get_album_url(playlist_id: str) -> str:
        """Construct a YouTube Music playlist URL from a playlist ID.

        Args:
            playlist_id: The YouTube Music playlist ID of the album/EP.

        Returns:
            The full YouTube Music URL for the album/EP playlist.

        """
        if not playlist_id:
            raise ValueError("Playlist ID cannot be empty")
        return r"https://music.youtube.com/playlist?list=" + playlist_id

    @staticmethod
    @log_event("youtube._get_albums")
    def _get_albums(
            artist_details: dict,
            channel_id: str,
            get_eps: bool = True,
            get_songs: bool = False,
            session_id: str | None = None
    ) -> list[str]:
        """Fetch album IDs from artist details.

        Args:
            artist_details: The details dictionary of the artist, as returned
                by ytmusic.get_artist
            channel_id: The YouTube channel ID of the artist, used for API calls
                and fallback scanning.
            get_eps: Whether to include EPs/singles in the results.
            get_songs: Whether to include individual songs that are not part of
                albums/EPs in the results.
            session_id: Optional session ID for logging.

        Returns:
            A list of album playlist IDs and optionally EP playlist IDs and
                song video IDs.

        """
        album_ids: list[str] = []

        albums_list: list[dict[str, Any]] = []
        params = ytmusic.get_artist(channel_id)
        try:
            albums_list = ytmusic.get_artist_albums(
                channel_id, limit=None, params=params,
            ) or []
        except Exception:
            albums_list = []

        if not albums_list or len(albums_list) < 50:
            album_section = artist_details.get("albums", {}) or {}
            collected = YoutubeAlbumFetcher._collect_section_results(album_section)
            if collected:
                seen = set()
                merged: list[dict[str, Any]] = []
                for a in collected + albums_list:
                    pid = a.get(
                        "audioPlaylistId"
                    ) or a.get("browseId") or a.get("playlistId")
                    if pid and pid not in seen:
                        seen.add(pid)
                        merged.append(a)
                albums_list = merged

        if not albums_list:
            raise ValueError("No album details found")

        for album in albums_list:
            playlist_id = album.get(
                "audioPlaylistId"
            ) or album.get("browseId") or album.get("playlistId")
            if not playlist_id:
                continue
            album_ids.append(playlist_id)

        if get_eps:
            album_ids.extend(
                YoutubeAlbumFetcher.get_eps_and_songs(
                    artist_details,
                    channel_id=channel_id,
                    get_songs=get_songs,
                    session_id=session_id,
                )
            )

        seen = set()
        deduped: list[str] = []
        for aid in album_ids:
            if aid and aid not in seen:
                seen.add(aid)
                deduped.append(aid)

        return deduped

    @staticmethod
    @log_event("youtube._get_artist_details")
    def _get_artist_details(
        artist_id: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """Fetch artist details from YouTube Music by artist ID.

        Args:
            artist_id: The YouTube Music artist ID (channel ID).
            session_id: Optional session ID for logging.

        Returns:
            A dictionary containing the artist details as returned by
                ytmusic.get_artist.

        """
        return ytmusic.get_artist(artist_id)

    @staticmethod
    @log_event("youtube.get_album_songs")
    def get_album_songs(playlist_id: str, session_id: str | None = None) -> list[str]:
        """Fetch song URLs from a given album/playlist ID.

        Args:
            playlist_id: The YouTube Music playlist ID of the album/EP.
            session_id: Optional session ID for logging.

        Returns:
            A list of YouTube Music song URLs contained in the album/EP.

        """
        playlist = ytmusic.get_playlist(playlist_id, limit=None)
        tracks = playlist.get("tracks", []) if playlist else []

        songs: list[str] = []
        for track in tracks:
            video_id = track.get("videoId")
            if video_id:
                song_url = ("https://music.youtube.com/"
                            f"watch?v={video_id}&list={playlist_id}")
                songs.append(song_url)
        return songs

    @staticmethod
    @log_event("youtube.get_eps")
    def get_eps_and_songs(
            artist_details: dict,
            get_songs: bool = False,
            channel_id: str = "",
            session_id: str | None = None
    ) -> list[str]:
        """Fetch EPs (and optionally songs) from artist details.

        Args:
            artist_details: The details dictionary of the artist, as returned
                by ytmusic.get_artist
            get_songs: Whether to include individual songs that are not part
                of albums/EPs.
            channel_id: The YouTube channel ID of the artist, used for fallback
                scanning if 'singles' section is not present in artist_details.
            session_id: Optional session ID for logging.

        Returns:
            A list of EP playlist IDs and optionally song video IDs.

        """
        eps: list[str] = []
        seen_ids = set()

        # Use continuation-aware collector for 'singles' section first
        singles_section = artist_details.get("singles", {}) or {}
        releases = YoutubeAlbumFetcher._collect_section_results(singles_section)

        # If no singles found in artist_details, scan full albums for singles/EPs
        if not releases:
            try:
                all_albums = ytmusic.get_artist_albums(channel_id, limit=None) or []
            except Exception:
                all_albums = []
            releases = [
                a for a in all_albums
                if (str(a.get(
                    "type", ""
                )).lower() in ("single", "ep") or a.get("isSingle") is True)
            ]

        for item in releases:
            playlist_id = item.get("browseId") or item.get(
                "audioPlaylistId"
            ) or item.get("playlistId")
            if not playlist_id or playlist_id in seen_ids:
                continue

            try:
                album_details = ytmusic.get_album(playlist_id)
            except Exception:
                continue

            track_count = len(album_details.get("tracks", []))

            if track_count <= 1 and not get_songs:
                continue

            audio_playlist_id = album_details.get("audioPlaylistId") or playlist_id
            if audio_playlist_id:
                eps.append(audio_playlist_id)
                seen_ids.add(playlist_id)

            if get_songs:
                for t in album_details.get("tracks", []):
                    vid = t.get("videoId")
                    if vid and vid not in seen_ids:
                        eps.append(vid)
                        seen_ids.add(vid)

        return eps
