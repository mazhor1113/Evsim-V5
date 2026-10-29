"""Pygame implementation of the backend-independent graphics interface."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pygame as pg

from config import (
    BIG_FONTSIZE,
    MAX_FPS,
    MID_FONTSIZE,
    SCREENSIZE,
    SIMULATION_WINDOW_POSITION,
    SIMULATION_WINDOW_SIZE,
    SMALL_FONTSIZE,
    UI_WINDOW_POSITION,
    UI_WINDOW_SIZE,
    WORLDSIZE,
)
from graphics.event import EventType, UIEvent
from paths import SPRITES_DIR

from typing import TYPE_CHECKING
from graphics.ui.widgets import Rect


class PygameBackend:
    """Manage pygame surfaces/assets and translate native events into UI events."""

    def __init__(self) -> None:
        """Initialize pygame, create surfaces, and prepare fonts and caches."""
        pg.init()
        pg.font.init()

        self.surfaces: dict[str, pg.Surface] = {}
        self.surfaces["main_surface"] = pg.display.set_mode(
            SCREENSIZE,
            pg.HWSURFACE | pg.DOUBLEBUF | pg.RESIZABLE,
        )
        self.surfaces["simulation_surface"] = pg.Surface(WORLDSIZE)
        self.surfaces["ui_surface"] = pg.Surface(UI_WINDOW_SIZE)

        self.clock = pg.time.Clock()
        self.fonts: dict[str, pg.font.Font] = {
            "font_big": pg.font.SysFont("arial", BIG_FONTSIZE),
            "font_mid": pg.font.SysFont("arial", MID_FONTSIZE),
            "font_small": pg.font.SysFont("arial", SMALL_FONTSIZE),
        }
        self.textures: dict[str, pg.Surface] = {}
        self._scaled_textures: dict[tuple[str, int, int], pg.Surface] = {}

    def compose_surfaces(self) -> None:
        """Composite UI and simulation surfaces onto the main display surface."""
        main_surface = self.surfaces["main_surface"]
        main_surface.blit(self.surfaces["ui_surface"], UI_WINDOW_POSITION)
        main_surface.blit(self.surfaces["simulation_surface"], SIMULATION_WINDOW_POSITION)

    def present(self) -> int:
        """Flip the display and return elapsed frame time in milliseconds."""
        pg.display.flip()
        elapsed_ms = self.clock.tick(MAX_FPS)
        return elapsed_ms

    def get_fps(self) -> int:
        """Return the rounded FPS measured by pygame's clock."""
        return round(self.clock.get_fps())

    def load_image(self, key: str, path: str) -> None:
        """Load an image relative to ``sprites/`` and store it under ``key``."""
        if key in self.textures:
            raise ValueError(f"Texture already loaded: {key}")

        image_path: Path = SPRITES_DIR / path
        if not image_path.is_file():
            raise FileNotFoundError(f"Texture not found: {image_path}")

        self.textures[key] = pg.image.load(str(image_path)).convert_alpha()

    def get_rect(
        self,
        texture_key: str,
        positioned_x: int,
        positioned_y: int,
    ) -> Rect:
        """Build a rectangle at ``(x, y)`` with the texture's native dimensions."""
        width, height = self.get_texture_size(texture_key)
        return Rect(positioned_x, positioned_y, width, height)

    def has_texture(self, texture_key: str) -> bool:
        """Return whether a texture key has been loaded by this backend."""
        return texture_key in self.textures

    def get_texture_size(self, texture_key: str) -> tuple[int, int]:
        """Return the native dimensions of a loaded texture."""
        texture = self.textures[texture_key]
        return texture.get_width(), texture.get_height()

    def draw_pixels(
        self,
        x: int,
        y: int,
        pixels: np.ndarray,
        scale: int,
        surface_key: str = "main_surface",
    ) -> None:
        """Blit a pixel array to the simulation surface and then to a target surface."""
        simulation_surface = self.surfaces["simulation_surface"]

        pg.surfarray.blit_array(simulation_surface, pixels)

        simulation_surface = pg.transform.scale_by(
                    simulation_surface,
                    scale,
                )
        
        self.surfaces[surface_key].blit(
            simulation_surface,
            (x, y),
        )

    def draw_texture(
        self,
        surface_key: str,
        texture_key: str,
        rect: Rect,
    ) -> None:
        """Draw a texture, scaling and caching it when its size differs from ``rect``."""
        texture = self.textures[texture_key]
        target_size = (max(1, rect.width), max(1, rect.height))

        if texture.get_size() != target_size:
            cache_key = (texture_key, target_size[0], target_size[1])
            if cache_key not in self._scaled_textures:
                self._scaled_textures[cache_key] = pg.transform.scale(
                    texture,
                    target_size,
                )
            texture = self._scaled_textures[cache_key]

        self.surfaces[surface_key].blit(texture, (rect.x, rect.y))

    def get_clip(self, surface_key: str) -> Rect:
        """Return the active clipping rectangle for a surface."""
        clip = self.surfaces[surface_key].get_clip()
        return Rect(clip.x, clip.y, clip.width, clip.height)

    def set_clip(self, surface_key: str, rect: Rect | None) -> None:
        """Set a surface's clip rectangle, or restore unrestricted clipping with ``None``."""
        surface = self.surfaces[surface_key]
        if rect is None:
            surface.set_clip(None)
            return
        surface.set_clip((rect.x, rect.y, rect.width, rect.height))

    def draw_text(
        self,
        surface_key: str,
        text: str,
        font_key: str,
        color: tuple[int, int, int],
        rect: Rect | tuple[int, int],
    ) -> None:
        """Render text and blit it at a rectangle's top-left or an ``(x, y)`` point."""
        text_surface = self.fonts[font_key].render(text, False, color)
        if isinstance(rect, Rect):
            position = (rect.x, rect.y)
        else:
            position = rect
        self.surfaces[surface_key].blit(text_surface, position)

    def fill_surface(self, surface_key: str, color: tuple[int, int, int]) -> None:
        """Fill the named surface with an RGB color."""
        self.surfaces[surface_key].fill(color)

    def get_events(self) -> list[UIEvent]:
        """Drain pygame's event queue and return normalized UI events."""
        events: list[UIEvent] = []

        for event in pg.event.get():
            if event.type == pg.QUIT:
                events.append(UIEvent(EventType.QUIT))
            elif event.type == pg.MOUSEBUTTONDOWN:
                events.append(
                    UIEvent(
                        type=EventType.MOUSE_DOWN,
                        x=event.pos[0],
                        y=event.pos[1],
                        button=event.button,
                    )
                )
            elif event.type == pg.MOUSEBUTTONUP:
                events.append(
                    UIEvent(
                        type=EventType.MOUSE_UP,
                        x=event.pos[0],
                        y=event.pos[1],
                        button=event.button,
                    )
                )
            elif event.type == pg.MOUSEMOTION:
                events.append(
                    UIEvent(
                        type=EventType.MOUSE_MOVE,
                        x=event.pos[0],
                        y=event.pos[1],
                    )
                )
            elif event.type == pg.KEYDOWN:
                events.append(
                    UIEvent(
                        type=EventType.KEY_DOWN,
                        key=pg.key.name(event.key),
                    )
                )
            elif event.type == pg.KEYUP:
                events.append(
                    UIEvent(
                        type=EventType.KEY_UP,
                        key=pg.key.name(event.key),
                    )
                )
            elif event.type == pg.MOUSEWHEEL:
                mouse_x, mouse_y = pg.mouse.get_pos()
                events.append(
                    UIEvent(
                        type=EventType.MOUSE_WHEEL,
                        x=mouse_x,
                        y=mouse_y,
                        wheel_x=event.x,
                        wheel_y=event.y,
                    )
                )
            elif event.type == pg.TEXTINPUT:
                events.append(
                    UIEvent(
                        type=EventType.TEXT_INPUT,
                        text=event.text,
                    )
                )
            elif event.type == pg.WINDOWRESIZED:
                events.append(
                    UIEvent(
                        type=EventType.RESIZE,
                        width=event.x,
                        height=event.y,
                    )
                )
            elif event.type == pg.WINDOWFOCUSLOST:
                events.append(UIEvent(EventType.WINDOW_FOCUS_LOST))

        return events

    def quit(self) -> None:
        """Shut down pygame and release its display resources."""
        pg.quit()
