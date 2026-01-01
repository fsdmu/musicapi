"""Theme for MusicAPI."""

from nicegui import ui


def apply_theme():
    """Apply theme to user interface."""
    ui.dark_mode(True)
    ui.add_head_html(
        """
        <style>
            /* 1. Root & Body */
            body { background-color: #17181F !important; color: #EEEDF0; }

            /* 2. FORCE DARK DROPDOWNS */
            body .q-menu,
            body .q-list,
            body .q-item {
                background-color: #1E1F29 !important;
                color: #EEEDF0 !important;
                border: 0.5px solid #333;
            }

            /* 3. Dropdown Hover/Active States */
            body .q-item:hover,
            body .q-item--active {
                background-color: #33343F !important;
                color: #CB69C1 !important;
            }

            /* 4. Dialogs & Cards */
            .q-dialog__inner .q-card {
                background-color: #1E1F29 !important;
                color: #EEEDF0 !important;
                border: 1px solid #333;
            }

            /* 5. Base Input Colors (Keep Text White) */
            .q-field--dark .q-field__native,
            .q-field--dark .q-field__input {
                color: #EEEDF0 !important;
            }

            .q-field--dark .q-field__label {
                color: #EEEDF0;
            }

            /* 6. Buttons & Switches */
            .pink-btn {
                background-color: #CB69C1 !important;
                color: #EEEDF0 !important;
            }

            .q-toggle__inner--truthy .q-toggle__thumb {
                color: #CB69C1 !important;
            }

            .q-toggle__inner--truthy .q-toggle__track {
                background: #CB69C1 !important;
                opacity: 0.6;
            }

            /* 7. Focus Highlights (The Pink Shade) */
            /* This changes the border/underline and label color on focus */
            .q-field--focused .q-field__control {
                color: #CB69C1 !important;
            }

            .q-field--focused .q-field__label {
                color: #CB69C1 !important;
            }

            /* Icons, dropdown arrows, and Quasar primary text */
            .q-field__marginal, .text-primary {
                color: #CB69C1 !important;
            }

            /* 8. Icons */
            .q-icon {
                color: #CB69C1 !important;
            }

        </style>
    """
    )
