"""Module to fetch album and song information from YouTube Music."""

from typing import Any

from ytmusicapi import YTMusic

from src.logging.event_logger import log_event

ytmusic = YTMusic()


class YoutubeAlbumFetcher:
    """A class to fetch album and song information from YouTube Music."""

    @staticmethod
    def _collect_section_results(section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect all items from a section, following continuation tokens when present.

        This handles several shapes returned by ytmusicapi: initial 'results' and
        various continuation token structures. For each continuation token it calls
        ytmusic.get_continuation(...) and extracts list-like results.
        """
        items: List[Dict[str, Any]] = []
        if not section:
            return items

        # initial results
        items.extend(section.get("results", []) if isinstance(section.get("results", []), list) else [])

        # collect explicit 'continuations' structures
        continuations = section.get("continuations", []) or []
        # try also 'continuation' / 'nextContinuationData' single-token shapes
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
            token = cont.get("continuation") or cont.get("token") or cont.get("nextContinuationData", {}).get("continuation")
            if not token:
                continue
            try:
                next_page = ytmusic.get_continuation(token)
            except Exception:
                break

            if isinstance(next_page, dict):
                # common direct list
                if "results" in next_page and isinstance(next_page.get("results"), list):
                    items.extend(next_page.get("results", []))
                    continue

                # nested containers
                for container_key in ("albums", "singles", "continuationContents", "contents"):
                    container = next_page.get(container_key)
                    if isinstance(container, dict) and isinstance(container.get("results"), list):
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
    @log_event("youtube._get_albums")
    def _get_albums(
            artist_details: dict,
            channel_id: str,
            get_eps: bool = True,
            get_songs: bool = False,
            session_id: str | None = None
    ) -> list[str]:
        album_ids: List[str] = []

        # Primary attempt: request full album list from API
        albums_list: List[Dict[str, Any]] = []
        try:
            albums_list = ytmusic.get_artist_albums(channel_id, limit=None) or []
        except Exception:
            albums_list = []

        # If API returned very few items or none, try to collect continuations from artist_details
        if not albums_list or len(albums_list) < 50:
            album_section = artist_details.get("albums", {}) or {}
            collected = YoutubeAlbumFetcher._collect_section_results(album_section)
            # if collected looks like album dicts, prefer collected; otherwise keep existing
            if collected:
                # normalize collected structure into list of dicts
                # some continuation items may already match get_artist_albums items
                # prepend collected to ensure we include anything missing
                # avoid duplicating by building a map by browseId/audioPlaylistId
                seen = set()
                merged: List[Dict[str, Any]] = []
                for a in collected + albums_list:
                    pid = a.get("audioPlaylistId") or a.get("browseId") or a.get("playlistId")
                    if pid and pid not in seen:
                        seen.add(pid)
                        merged.append(a)
                albums_list = merged

        if not albums_list:
            raise ValueError("No album details found")

        for album in albums_list:
            playlist_id = album.get("audioPlaylistId") or album.get("browseId") or album.get("playlistId")
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

        # Deduplicate while preserving order
        seen = set()
        deduped: List[str] = []
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
        return ytmusic.get_artist(artist_id)

    @staticmethod
    @log_event("youtube.get_album_songs")
    def get_album_songs(playlist_id: str, session_id: str | None = None) -> list[str]:
        playlist = ytmusic.get_playlist(playlist_id, limit=None)
        tracks = playlist.get("tracks", []) if playlist else []

        songs: List[str] = []
        for track in tracks:
            video_id = track.get("videoId")
            if video_id:
                song_url = f"https://music.youtube.com/watch?v={video_id}&list={playlist_id}"
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
        eps: List[str] = []
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
                if (str(a.get("type", "")).lower() in ("single", "ep") or a.get("isSingle") is True)
            ]

        for item in releases:
            playlist_id = item.get("browseId") or item.get("audioPlaylistId") or item.get("playlistId")
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
