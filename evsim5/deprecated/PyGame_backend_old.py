from config import BG_COLOR
import pygame as pg
import numpy as np
from typing import Annotated
import numpy.typing as npt
from numba import njit

# без комментариев
canvasType=Annotated[npt.NDArray[np.uint8],('screen_width','screen_length',3)]

@njit(cache=True)
def fill_canvas(canvas, color):
    for x in range(canvas.shape[0]):
        for y in range(canvas.shape[1]):
            canvas[x,y,0] = color[0]
            canvas[x,y,1] = color[1]
            canvas[x,y,2] = color[2]
    return canvas

def draw(canvas:canvasType, simulation_window_position:tuple, main_surface:pg.surface, canvas_surface:pg.surface, pixelsize:int):
    main_surface.fill('Grey')
    pg.surfarray.blit_array(canvas_surface, canvas)

    main_surface.blit(canvas_surface, simulation_window_position)


def init_drawer(worldsize:tuple, screensize:tuple, simulation_window_size:tuple, big_fontsize:int, mid_fontsize:int, small_fontsize:int, uisize:tuple):
    pg.init()
    pg.font.init()

    pixelsize = min(simulation_window_size[0]/worldsize[0],simulation_window_size[1]/worldsize[1])

    main_surface = pg.display.set_mode(screensize, pg.HWSURFACE|pg.DOUBLEBUF|pg.RESIZABLE)
    canvas_surface = pg.Surface(worldsize)
    ui_surface = pg.Surface(uisize)

    if pixelsize > 1:
            canvas_surface = pg.transform.scale_by(canvas_surface, pixelsize)

    canvas = np.zeros((worldsize[0],worldsize[1],3), dtype=np.uint8)
    canvas[:] = BG_COLOR

    CLOCK = pg.time.Clock()
    TEXT_BIGFONT = pg.font.SysFont('arial', big_fontsize)
    TEXT_MIDFONT = pg.font.SysFont('arial', mid_fontsize)
    TEXT_SMALLFONT = pg.font.SysFont('arial', small_fontsize)

    return pixelsize, main_surface, canvas_surface, ui_surface, canvas, CLOCK, TEXT_BIGFONT, TEXT_MIDFONT, TEXT_SMALLFONT


def update_drawer(worldsize:tuple, SCREENSIZE:tuple=(1200,700), FONTSIZE:int=36):
    
    pixelsize=min(SCREENSIZE[0]/worldsize[0],SCREENSIZE[1]/worldsize[1])

    TEXT=pg.font.SysFont('arial', FONTSIZE)

    return pixelsize, TEXT, SCREENSIZE

@njit(cache=True)
def __DEBUG__PROJECT_FIELD_TO_CANVAS(worldsize, type_field, canvas, BOT_CELLTYPE, ORGANIC_CELLTYPE, AIR_CELLTYPE):
    for x in range(worldsize[0]):
        for y in range(worldsize[1]):
            if type_field[x,y] != AIR_CELLTYPE:
                if type_field[x,y] == BOT_CELLTYPE:
                    canvas[x,y] = 255,0,0
                elif type_field[x,y] == ORGANIC_CELLTYPE:
                    canvas[x,y] = 100,100,100
    return canvas