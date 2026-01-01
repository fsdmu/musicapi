"""Web UI for adding YouTube albums and artists to MeTube."""

import logging
import src.logging_config  # noqa: F401
from nicegui import ui
from src.url_handler import UrlHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- THEME STYLING ---
ui.add_head_html('''
    <style>
        body { background-color: #17181F; color: #EEEDF0; }
        .q-drawer { background-color: #1E1F29 !important; color: #EEEDF0 !important; }
        .q-card { background-color: #1E1F29 !important
        ; color: #EEEDF0 !important; border: 1px solid #333; }
        .q-field__label, .q-field__native, .q-field__prefix, .q-field__suffix
        , .q-field__input {
            color: #EEEDF0 !important;
        }
    </style>
''')

# --- SIDEBAR (Right Drawer) ---
with ui.right_drawer(
        top_corner=True, value=False
).style("background-color: #1E1F29; border-left: 1px solid #333") as right_drawer:
    ui.label("Settings").classes("text-xl mb-4")
    audio_format = ui.select(
        ["mp3", "wav", "flac", "m4a"], label="Select download format", value="mp3"
    ).props('dark standout color=pink-4').classes("w-full")

# --- DIALOGS ---
with ui.dialog() as help_dialog:
    with ui.card().classes("w-96"):
        ui.label("How to use MeTube Adder").classes("text-h6 text-[#CB69C1]")
        ui.markdown(
            """
        - **Paste URL:** Put a YouTube Artist or Album link in the box.
        - **Auto Download:** If on, future albums by this artist are tracked.
        - **Settings:** Click the code icon (top-right) for audio formats.
        - **Submit:** Adds the content to your MeTube instance.
        """
        )
        ui.button(
            "Close", on_click=help_dialog.close
        ).props('flat').classes("ml-auto text-[#EEEDF0]")

# --- HEADER BUTTONS ---
with ui.row().classes("absolute top-2 right-2 items-center"):
    ui.button(
        icon="help", on_click=help_dialog.open
    ).props("round flat").classes("text-[#EEEDF0]")
    ui.button(
        icon="code", on_click=lambda: right_drawer.toggle()
    ).props("round flat").classes("text-[#EEEDF0]")

# --- MAIN UI CONTENT ---
with ui.column().classes('w-full max-w-xl mx-auto items-center p-8 gap-4 mt-12'):
    ui.label("MeTube Album Adder").classes("text-3xl font-bold mb-4 text-[#CB69C1]")

    with ui.column().classes('w-full gap-1'):
        ui.label("Enter YouTube URL here:").classes(
            "text-xs uppercase tracking-wider opacity-70 ml-1")
        url_input = ui.input(placeholder="https://youtube.com/...") \
            .props('outlined dark color=pink-4') \
            .classes('w-full') \
            .style('color: #EEEDF0 !important;')

    auto_download_toggle = ui.switch(
        "Auto Download artists' future albums", value=False
    ).props('color=pink-4').classes('text-[#EEEDF0] mt-2')

    # SUBMIT BUTTON
    ui.button("Submit", on_click=lambda: on_submit()) \
        .style(
        'background-color: #CB69C1 !important; color: #EEEDF0 '
        '!important; width: 100%; height: 50px; '
        'font-weight: bold; font-size: 1.1em; margin-top: 10px;'
    )


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
                with ui.row().classes('w-full justify-end'):
                    ui.button(
                        "No", on_click=lambda: dialog.submit("No")
                    ).props('flat').classes('text-[#EEEDF0]')
                    ui.button(
                        "Yes", on_click=lambda: dialog.submit("Yes")
                    ).classes('bg-[#CB69C1] text-[#EEEDF0]')

            result = await dialog
            if result != "Yes":
                return

        handler.download(
            url=url,
            auto_download=auto_download_toggle.value,
            add_without_download=False,
            download_format=audio_format.value,
        )

        ui.notify(f"Successfully added: {url}", color="positive")
        url_input.value = ""

    except Exception as e:
        ui.notify(f"Error: {e}", color="negative")
        return


ui.run(host="0.0.0.0", port=8080)
