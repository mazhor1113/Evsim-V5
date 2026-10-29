"""Loading helpers for built-in placeholder textures."""

from graphics.protocols import GraphicsBackend


def load_textures(backend: GraphicsBackend) -> None:
    """Load the images expected by the current widgets.
    Texture paths are relative to the project's ``sprites/`` directory.
    """
    backend.load_image("placeholder_button", "placeholders/button.png")
    backend.load_image("placeholder_button_pressed", "placeholders/button_pressed.png")
    backend.load_image("placeholder_checkbox_on", "placeholders/checkbox_on.png")
    backend.load_image("placeholder_checkbox_off", "placeholders/checkbox_off.png")
    backend.load_image("placeholder_toggle_button_on", "placeholders/toggle_button_on.png")
    backend.load_image("placeholder_toggle_button_off", "placeholders/toggle_button_off.png")
    backend.load_image("placeholder_slider_body", "placeholders/slider_body.png")
    backend.load_image("placeholder_slider_thumb", "placeholders/slider_thumb.png")
    backend.load_image("placeholder_window_bg", "placeholders/window_bg.png")
    backend.load_image("placeholder_window_close", "placeholders/window_close.png")
    backend.load_image("placeholder_window_hide", "placeholders/window_hide.png")
    backend.load_image("placeholder_window_resize", "placeholders/window_resize.png")
    backend.load_image("placeholder_window_title", "placeholders/window_title.png")
    backend.load_image("placeholder_panel_bg", "placeholders/panel_bg.png")
    backend.load_image("selection", "placeholders/selection.png")
