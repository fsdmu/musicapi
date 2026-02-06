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
                    value="flac",
                )
                .props("dark")
                .classes("w-full")
                .style("--q-primary: #CB69C1;")
            )

    def toggle(self):
        """Toggle SettingsDrawer state."""
        self.drawer.toggle()


class HelpDialog:
    """Help dialog component for the MusicAPI user interface."""

    def __init__(self):
        """Initialize the HelpDialog."""
        with ui.dialog() as self.dialog:
            with ui.card().classes("w-[500px] bg-[#1E1F29] border border-[#333]"):
                ui.label("Help & Privacy").classes("text-h6 text-[#CB69C1]")

                with ui.element("div").classes("text-[#EEEDF0]"):
                    ui.markdown(
                        """
                        ### 📖 Usage Instructions
                        - **Paste URL:** YouTube Artist, Album/EP/Playlist or Song link.
                        - **Auto Download:** Tracks future Album/EP releases 
                            of the artist.
                        - **Settings:** Click the code icon for additional options.

                        ---

                        ### 🔒 Logging Policy
                        To ensure service stability certain events are logged:

                        * **What is logged:** Page views, button clicks,
                            any text in the url input field after you click 'submit'
                            , Browser User-Agent, and function
                            execution speeds.
                        * **No PII:** We do **not** log your IP address.
                        * **Redaction:** Any sensitive data is **masked**.
                            Our system automatically scrubs values associated with
                            keys like `password`, `token`, `secret`, or `auth`.
                        * **Session ID:** A temporary ID (cookie) groups logs to help
                            me fix bugs without tracking you across the web.
                        * **Storage:** Logs are stored in a private PostgresSQL
                            database and are periodically deleted.
                        * **Disclaimer:** This is a private, free and
                            open-source project. Every privacy acknowledgement
                            by this application is made in good faith
                            and best effort, but there are no guarantees. 
                            The code is verifiable under
                            [this link](https://github.com/fsdmu/musicapi).
                    """
                    )

                with ui.row().classes("w-full justify-end mt-4"):
                    ui.button("Close", on_click=self.dialog.close).props(
                        "flat"
                    ).classes("text-[#EEEDF0]").style("--q-primary: #CB69C1;")

    def open(self):
        """Open the help dialog."""
        self.dialog.open()
