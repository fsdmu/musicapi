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

            /* 2. FORCE DARK DROPDOWNS (The "Final Boss" CSS) */
            /* We target the body-level menu container directly */
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

            /* 5. Inputs & Labels */
            .q-field--dark .q-field__label,
            .q-field--dark .q-field__native,
            .q-field--dark .q-field__control {
                color: #EEEDF0 !important;
            }

            /* 6. Utility Classes */
            .pink-btn {
                background-color: #CB69C1 !important;
                color: #EEEDF0 !important;
            }
        </style>
    """
    )
