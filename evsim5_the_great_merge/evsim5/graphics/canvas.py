"""Numba-accelerated pixel canvas used by the simulation renderer."""

from __future__ import annotations

import numpy as np
from numba import njit

from config import *

from typing import TYPE_CHECKING
from graphics.ui.widgets import Rect, Color


@njit(cache=True)
def _set_background(
    width: int,
    height: int,
    pixels: np.ndarray,
    background_mask: np.ndarray,
    color: Color,
) -> None:
    """Fill masked pixels with ``color``; pixels already marked dirty are kept."""
    for x in range(width):
        for y in range(height):
            if background_mask[x, y]:
                pixels[x, y] = color


@njit(cache=True)
def _set_pixel(
    pixels: np.ndarray,
    background_mask: np.ndarray,
    x: int,
    y: int,
    color: Color,
) -> None:
    """Write one RGB pixel and mark it in the mask."""
    pixels[x, y] = color
    background_mask[x, y] = False


class Canvas:
    """Store simulation pixels and a mask of pixels that need background filling."""

    def __init__(
        self,
        size: tuple[int, int] = WORLDSIZE,
        position: tuple[int, int] = SIMULATION_WINDOW_POSITION,
        scale: int = 1,
        background_color: Color = BG_COLOR,
    ) -> None:
        """Allocate a ``width × height`` RGB array and initialize its background."""

        self.width: int = size[0]
        self.height: int = size[1]
        self.x: int = position[0]
        self.y: int = position[1]

        self.rect: Rect = Rect(
            self.x, 
            self.y, 
            self.width * scale, 
            self.height * scale,
        )

        self.scale: int = scale

        self.pixels = np.empty((self.width, self.height, 3), dtype=np.uint8)
        self.background_mask = np.full((self.width, self.height), True, dtype=np.bool_)

        self.set_background(background_color)

    def set_background(self, color: Color) -> None:
        """Fill pixels that remain marked in the background mask."""
        _set_background(
            self.width,
            self.height,
            self.pixels,
            self.background_mask,
            color,
        )

    def set_pixel(
            self,
            x: int, 
            y: int, 
            color: Color,
    ) -> None:
        _set_pixel(
            self.pixels, 
            self.background_mask, 
            x, 
            y, 
            color,
            )
