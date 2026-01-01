"""Logic for MusicAPI user interface."""

from nicegui import ui
from src.url_handler import UrlHandler


async def process_submission(url_input, auto_download, audio_format):
    """Logic for handling the URL submission."""
    try:
        url = str(url_input.value).strip()
        if not url:
            ui.notify("Please enter a YouTube URL", color="negative")
            return

        handler = UrlHandler.get_handler(url)
        warning = handler.get_warning(url)

        if warning:
            if not await show_warning_dialog(warning):
                return

        handler.download(
            url=url,
            auto_download=auto_download,
            add_without_download=False,
            download_format=audio_format,
        )

        ui.notify(f"Successfully added: {url}", color="positive")
        url_input.value = ""

    except Exception as e:
        ui.notify(f"Error: {e}", color="negative")


async def show_warning_dialog(message: str) -> bool:
    """Show confirmation dialog and return the result."""
    with ui.dialog() as dialog, ui.card():
        ui.label(message + "\nDo you want to continue?")
        with ui.row().classes("w-full justify-end"):
            ui.button("No", on_click=lambda: dialog.submit(False)).props("flat")
            ui.button("Yes", on_click=lambda: dialog.submit(True)).classes("pink-btn")

    result = await dialog
    return result
