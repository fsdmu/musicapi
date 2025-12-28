"""Web UI for adding YouTube albums and artists to MeTube."""

import logging

import src.logging_config  # noqa: F401

from nicegui import ui

from src.url_handler import UrlHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


with ui.right_drawer(top_corner=True, value=False).style(
    "background-color: #ececec"
) as right_drawer:
    # add_without_download = ui.switch(
    #     "Add artist to download future albums without queuing downloads now."
    #     "This will prevent downloading any previous album of the artist.",
    #     value=False,
    # )
    audio_format = ui.select(
        ["mp3", "wav", "flac", "m4a"], label="Select download format", value="mp3"
    ).classes('w-full')


ui.button(icon="code", on_click=lambda: right_drawer.toggle()).classes(  # type: ignore
    "absolute top-2 right-2"
)

ui.label("Enter YouTube URL here:")
url_input = ui.input(placeholder="YouTube URL")

auto_download_toggle = ui.switch("Auto Download artists' future albums", value=False)

with ui.dialog() as help_dialog, ui.card().classes("w-96"):
    ui.label("How to use MeTube Adder").classes("'text-h6")
    ui.markdown(
        """
    - **Paste URL:** Put a YouTube Artist or Album link in the box.
    - **Auto Download:** If on, future albums by this artist are tracked and
        downloaded automatically.
    - **Developer Settings:** Click the code icon (top-right) to change audio formats.
    - **Submit:** Adds the content to your MeTube instance.
    """
    )
    ui.button("Close", on_click=help_dialog.close).classes("ml-auto")

with ui.row().classes("absolute top-2 right-2 items-center"):
    ui.button(icon="help", on_click=help_dialog.open).props("round flat color=grey")

    ui.button(icon="code", on_click=lambda: right_drawer.toggle()).props("round flat")


async def on_submit():
    """Handle the submission of a YouTube URL."""
    try:
        url = str(url_input.value).strip()
        if not url:
            ui.notify("Please enter a YouTube URL", color="negative")
            return

        handler = UrlHandler.get_handler(url)
        warning = handler.get_warning(url)

        if warning:
            with ui.dialog() as dialog, ui.card():
                ui.label(warning + "\nDo you want to continue?")
                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: dialog.submit("No"))

            result = await dialog
            if result != "Yes":
                return
        handler.download(
            url=url,
            auto_download=auto_download_toggle.value,
            #       add_without_download=add_without_download.value,
            add_without_download=False,
            download_format=audio_format.value,
        )

        url_input.value = ""

    except Exception as e:
        ui.notify(f"Error: {e}", color="negative")
        return


ui.button("Submit", on_click=on_submit)


ui.run(host="0.0.0.0", port=8080)
