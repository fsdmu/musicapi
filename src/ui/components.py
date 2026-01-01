"""Components for the MusicAPI user interface."""

from nicegui import ui


class SettingsDrawer:
    """Settings drawer component for the MusicAPI user interface."""

    def __init__(self):
        """Initialize the SettingsDrawer."""
        with ui.right_drawer(top_corner=True, value=False).style(
            "background-color: #1E1F29; border-left: 1px solid #333"
        ) as self.drawer:
            ui.label("Settings").classes("text-xl mb-4 text-[#EEEDF0]")

            self.audio_format = (
                ui.select(
                    ["mp3", "wav", "flac", "m4a"],
                    label="Select download format",
                    value="mp3",
                )
                .props("dark color=pink-4")
                .classes("w-full")
            )

    def toggle(self):
        """Toggle SettingsDrawer state."""
        self.drawer.toggle()


class HelpDialog:
    """Help dialog component for the MusicAPI user interface."""

    def __init__(self):
        """Initialize the HelpDialog."""
        with ui.dialog() as self.dialog:
            with ui.card().classes("w-96 bg-[#1E1F29] border border-[#333]"):
                ui.label("How to use MeTube Adder").classes("text-h6 text-[#CB69C1]")

                with ui.element("div").classes("text-[#EEEDF0]"):
                    ui.markdown(
                        """
                        - **Paste URL:** YouTube Artist or Album link.
                        - **Auto Download:** Tracks future releases.
                        - **Settings:** Click the code icon for formats.
                    """
                    )

                with ui.row().classes("w-full justify-end mt-4"):
                    ui.button("Close", on_click=self.dialog.close).props(
                        "flat"
                    ).classes("text-[#EEEDF0]")

    def open(self):
        """Open the help dialog."""
        self.dialog.open()
