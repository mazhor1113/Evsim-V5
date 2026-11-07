"""Structural interfaces shared by the graphics backend and UI widgets.

These protocols describe the methods a compatible object must provide. They do
not contain implementations and do not require classes to inherit from them.
"""

from __future__ import annotations

from typing import Protocol, Literal, TypeAlias

import numpy as np

from graphics.event import UIEvent
from graphics.ui.widgets import Rect, CoordinateSpace

class GraphicsBackend(Protocol):
    """Operations the UI and simulation need from a rendering backend.

    A backend owns surfaces, textures, fonts, presentation and conversion of
    native window events into backend-independent ``UIEvent`` objects.
    """

    def compose_surfaces(self) -> None:
        """Composite the simulation and UI surfaces onto the main surface."""
        ...

    def present(self) -> int:
        """Present the completed frame and return elapsed frame time in ms."""
        ...

    def get_fps(self) -> int:
        """Return the backend's measured frames per second."""
        ...

    def load_image(self, key: str, path: str) -> None:
        """Load an image asset under a unique texture key."""
        ...

    def get_rect(self, texture_key: str, positioned_x: int, positioned_y: int) -> Rect:
        """Create a rectangle at a position using a texture's native dimensions."""
        ...

    def has_texture(self, texture_key: str) -> bool:
        """Return whether the named texture has been loaded."""
        ...

    def get_texture_size(self, texture_key: str) -> tuple[int, int]:
        """Return a texture's width and height in pixels."""
        ...

    def draw_pixels(
        self,
        x: int,
        y: int,
        pixels: np.ndarray,
        scale: int,
        surface_key: str = "main_surface",
    ) -> None:
        """Copy a pixel array to the simulation surface and composite it."""
        ...

    def draw_texture(self, surface_key: str, texture_key: str, rect: Rect) -> None:
        """Draw a texture scaled to fit ``rect`` on the named surface."""
        ...

    def draw_text(
        self,
        surface_key: str,
        text: str,
        font_key: str,
        color: tuple[int, int, int],
        rect: Rect | tuple[int, int],
    ) -> None:
        """Render text at the top-left of the supplied rectangle or position."""
        ...

    def fill_surface(self, surface_key: str, color: tuple[int, int, int]) -> None:
        """Fill a named surface with an RGB color."""
        ...

    def get_clip(self, surface_key: str) -> Rect:
        """Return the current clipping rectangle for a surface."""
        ...

    def set_clip(self, surface_key: str, rect: Rect | None) -> None:
        """Set a surface's clipping rectangle, or clear clipping with ``None``."""
        ...

    def get_events(self) -> list[UIEvent]:
        """Return pending native events converted to backend-independent events."""
        ...

    def quit(self) -> None:
        """Release backend resources and shut down the graphics library."""
        ...


class UIElement(Protocol):
    """Minimum interface required for an object managed by ``UIManager``."""

    rect: Rect
    visible: bool
    enabled: bool
    coordinate_space: CoordinateSpace

    def draw(
        self,
        backend: GraphicsBackend,
        offset: tuple[int, int] = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Draw this element using a parent offset and target surface."""
        ...

    def handle_event(self, event: UIEvent) -> None:
        """Update element state in response to a normalized input event."""
        ...
