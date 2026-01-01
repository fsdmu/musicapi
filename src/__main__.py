"""User interface for the MusicAPi."""
import logging
import src.logging_config  # noqa: F401
from nicegui import ui

from src.ui.theme import apply_theme
from src.ui.components import SettingsDrawer, HelpDialog
from src.ui.logic import process_submission

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MusicApiApp:
    """Class for the MusicAPI user interface."""

    def __init__(self):
        """Initialize the MusicApiApp."""
        apply_theme()

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
        with ui.column().classes("w-full max-w-xl mx-auto items-center p-8 gap-4 mt-12"):
            ui.label("MusicAPI").classes("text-3xl font-bold mb-4 text-[#CB69C1]")

            with ui.column().classes("w-full gap-1"):
                ui.label("Enter YouTube URL:").classes("text-xs uppercase opacity-70 ml-1")
                self.url_input = ui.input(placeholder="https://youtube.com/...") \
                    .props('outlined dark color=pink-4') \
                    .classes("w-full")

            self.auto_dl = ui.switch("Auto Download artists' future albums", value=False) \
                .props("color=pink-4").classes("mt-2")

            ui.button("Submit", on_click=self.handle_click) \
                .classes("pink-btn w-full h-[50px] font-bold text-lg mt-4")

    async def handle_click(self):
        """Handle a download submission."""
        await process_submission(
            self.url_input,
            self.auto_dl.value,
            self.settings.audio_format.value
        )


@ui.page('/')
def main_page():
    MusicApiApp()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8080, title="MusicAPI")
