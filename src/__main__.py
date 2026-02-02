"""User interface for the MusicAPi."""

import logging
import uuid
from starlette.requests import Request
from starlette.responses import Response

from src.logging.log_database_connector import LogDatabaseConnector
from src.logging_config import setup_logging, stop_logging
from nicegui import ui, app

from src.ui.theme import apply_theme
from src.ui.components import SettingsDrawer, HelpDialog
from src.ui.logic import process_submission
from src.logging.event_logger import log_event

logger = logging.getLogger("app.music_api_ui")
logger.setLevel(logging.INFO)

latest_url_value = ""

THRESHOLD = 4


class MusicApiApp:
    """Class for the MusicAPI user interface."""

    def __init__(self, session_id: str | None = None):
        """Initialize the MusicApiApp."""
        apply_theme()

        self.session_id = session_id

        self.settings = SettingsDrawer()
        self.help = HelpDialog()

        self.build_header()
        self.build_main_content()

    def build_header(self):
        """Build the header for the MusicAPI user interface."""
        with ui.row().classes("absolute top-2 right-2 items-center"):
            ui.button(icon="help", on_click=self.help.open).props("round flat")
            ui.button(icon="code", on_click=self.settings.toggle).props("round flat")

    def build_main_content(self):
        """Build the main content for the MusicAPI user interface."""
        @log_event("url.input.change")
        def _on_url_change(value: str, session_id: str | None = None):
            """Handler invoked on URL input changes; logged by decorator.

            Returning a small dict makes it easier to inspect results in logs.
            """
            val = (str(value) or "").strip()
            return {"value": val}

        def _on_update(value):
            v = (str(value.value) or "").strip()
            global latest_url_value

            if len(v) <= THRESHOLD:
                return

            if latest_url_value in v and len(v.replace(latest_url_value, "")) <= THRESHOLD:
                return
            latest_url_value = v
            _on_url_change(v, session_id=self.session_id)

        with ui.column().classes(
            "w-full max-w-xl mx-auto items-center p-8 gap-4 mt-12"
        ):
            ui.label("MusicAPI").classes("text-3xl font-bold mb-4 text-[#CB69C1]")

            with ui.column().classes("w-full gap-1"):
                ui.label("Enter YouTube URL:").classes(
                    "text-xs uppercase opacity-70 ml-1"
                )
                self.url_input = (
                    ui.input(placeholder="https://youtube.com/...", on_change=_on_update)
                    .props("outlined dark color=pink-4")
                    .classes("w-full")
                )

            self.auto_dl = (
                ui.switch("Auto Download artists' future albums", value=False)
                .props("color=#CB69C1")
                .classes("mt-2")
            )

            # ensure submit handler logs and receives session_id
            ui.button(
                "Submit",
                on_click=lambda: self.handle_click(session_id=self.session_id),
            ).props("color=#CB69C1").classes("pink-btn w-full h-[50px] font-bold text-lg mt-4")


    @log_event("submit.click")
    async def handle_click(self, session_id: str | None = None):
        """Handle a download submission. session_id is passed to logging wrapper."""
        await process_submission(
            self.url_input,
            self.auto_dl.value,
            self.settings.audio_format.value,
            session_id=session_id,
        )


@log_event("page.view")
def _log_page_view(session_id: str | None, client_ip: str | None, user_agent: str, created: bool):
    """Emit a structured page.view event via the log_event wrapper.

    The decorator will produce start/end entries; returning a payload makes it
    included in the event meta.
    """
    return {
        "client": {"ip": client_ip, "user_agent": user_agent},
        "session": {"id": session_id, "created": created},
    }


@ui.page("/")
def main_page(request: Request, response: Response) -> None:
    """Start user interface for the MusicAPi.

    Args:
        request: The incoming HTTP request.
        response: The HTTP response to be sent.

    """
    # create or reuse session id cookie
    session_id = request.cookies.get("session_id")
    created = False
    if not session_id:
        session_id = str(uuid.uuid4())
        # HttpOnly, secure flag left to deployment; Lax same-site is a reasonable default
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax", max_age=30 * 24 * 3600)
        created = True

    try:
        client_ip = request.client.host if request.client else None
    except Exception:
        client_ip = None
    user_agent = request.headers.get("user-agent", "")

    # Use the logging wrapper instead of manual logger.info
    _log_page_view(session_id=session_id, client_ip=client_ip, user_agent=user_agent, created=created)

    # Build the UI, pass session_id for handlers to use
    MusicApiApp(session_id=session_id)

app.on_shutdown(stop_logging)

if __name__ in {"__main__", "__mp_main__"}:
    setup_logging(LogDatabaseConnector())
    ui.run(host="0.0.0.0", port=8080, title="MusicAPI", uvicorn_logging_level="warning")
