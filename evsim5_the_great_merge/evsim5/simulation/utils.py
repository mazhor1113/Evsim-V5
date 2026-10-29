from config import *
import pygame as pg
from drawer import draw, canvasType, fill_canvas
import numpy as np
from numpy import random as r
from numba import njit
from simulation.engine import bot_dtype
from ui import handle_ui

def init_rng(RANDOMIZE_SEED, SEED):
    if RANDOMIZE_SEED:
        SEED = r.randint(0, 65536)
    r.seed(SEED)
    return SEED

@njit(cache=True)
def rgb_bg_calc(i, speed, brightness):
    i *= speed
    brightness /= 100
    i = i%2304
    if i < 256:
        bg_color = i%256, 0, 0
    elif i < 512:
        bg_color = 255, (i%256)//2, 0
    elif i < 768:
        bg_color = 255, 128 + (i%256)//2, 0
    elif i < 1024:
        bg_color = 255 - i%256, 255, 0
    elif i < 1280:
        bg_color = 0, 255, i%256
    elif i < 1536:
        bg_color = 0, 255 - i%256, 255
    elif i < 1792:
        bg_color = (i%256)//2, 0, 255 - (i%256)//2
    elif i < 2048:
        bg_color = 128 + (i%256)//2, i%256, 128 + (i%256)//2
    elif i < 2304:
        bg_color = 255 - i%256, 255 - i%256, 255 - i%256
    bg_color = int(bg_color[0]*brightness), int(bg_color[1]*brightness), int(bg_color[2]*brightness)
    return bg_color

def DO_CYCLE_START(canvas:canvasType, BG_COLOR:tuple):
     canvas = fill_canvas(canvas, BG_COLOR)

def DO_CYCLE_END(popup_active:bool, GLOBAL_COUNTER:int, MAX_FPS:int, clock:pg.time.Clock, simulation_window_position:tuple, pixelsize:int, main_surface:pg.Surface, canvas_surface:pg.Surface, ui_surface:pg.Surface, buttons_data, sliders_data, popup_windows_data, push_buttons_data, UISIZE, UIPOSITION, canvas:canvasType, TEXT_BIGFONT:pg.font, TEXT_MIDFONT:pg.font, TEXT_SMALLFONT:pg.font):
    #действия главного цикла
    global SCREENSIZE
    clickpos = None
    releasepos = None
    draw(canvas, simulation_window_position, main_surface, canvas_surface, pixelsize)
    GLOBAL_COUNTER += 1

    for event in pg.event.get():
            if event.type==pg.QUIT:
                pg.quit()
            if event.type==pg.VIDEORESIZE:
                SCREENSIZE=event.dict['size']
            if pg.key.get_pressed()[pg.K_ESCAPE]:
                pg.quit()
            if event.type==pg.MOUSEBUTTONDOWN and event.button==1:
                clickpos=event.pos
            if event.type==pg.MOUSEBUTTONUP and event.button==1:
                releasepos=event.pos

    RGB_SPEED, popup_active = handle_ui(GLOBAL_COUNTER, TEXT_BIGFONT, TEXT_MIDFONT, TEXT_SMALLFONT, main_surface, ui_surface, UISIZE, UIPOSITION, clickpos, releasepos, buttons_data, sliders_data, popup_active, popup_windows_data, push_buttons_data)
    pg.display.flip()
    clock.tick(MAX_FPS)
    return GLOBAL_COUNTER, RGB_SPEED, SCREENSIZE, clickpos, popup_active

@njit(cache=True)
def push_bot_stack(bot, bot_position:tuple, bot_age:int, bot_energy:int, bot_genome_id:int,
                   bot_positions, bot_ages, bot_energies, bot_stack_top, bots):
    
    bot_stack_top += 1
    if bot_stack_top >= WORLD_VOLUME:
        raise OverflowError('bot_stack overflow')
    bot_id = bot_stack_top

    bot_positions[bot_id, 0] = bot_position[0]
    bot_positions[bot_id, 1] = bot_position[1]
    bot_ages[bot_id] = bot_age
    bot_energies[bot_id] = bot_energy

    bot[0]['id'] = np.uint32(bot_id)
    bot[0]['genome_id'] = np.uint32(bot_genome_id)

    bots[bot_id]['id'] = bot[0]['id']
    bots[bot_id]['genome_id'] = bot[0]['genome_id']
    bots[bot_id]['instruction_id'] = bot[0]['instruction_id']
    bots[bot_id]['reading_step'] = bot[0]['reading_step']
    bots[bot_id]['colorR'] = bot[0]['colorR']
    bots[bot_id]['colorG'] = bot[0]['colorG']
    bots[bot_id]['colorB'] = bot[0]['colorB']

    return bot_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots

@njit(cache=True)
def pull_bot_stack(bot_id,
                   bot_positions, bot_ages, bot_energies, bot_stack_top, bots, id_field):
    if bot_id == bot_stack_top:
        bot_stack_top -= 1
    else:
        x, y = bot_positions[bot_stack_top][0], bot_positions[bot_stack_top][1]
        bot_positions[bot_id] = x, y
        id_field[x, y] = bot_id
        bot_ages[bot_id] = bot_ages[bot_stack_top]
        bot_energies[bot_id] = bot_energies[bot_stack_top]
        bots[bot_id] = bots[bot_stack_top]
        bots[bot_id]['id'] = bot_id
        bot_stack_top -= 1
    return bot_positions, bot_ages, bot_energies, bot_stack_top, bots, id_field
@njit(cache=True)
def spawn_bot(bot, bot_position:tuple, bot_age:int, bot_energy:int, bot_genome_id:int,
              bot_positions, bot_ages, bot_energies, bot_stack_top, bots,
              type_field, id_field):
    x, y = bot_position[0], bot_position[1]
    if type_field[x, y] == AIR_CELLTYPE:
        bot_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots = push_bot_stack(bot, bot_position, bot_age, bot_energy, bot_genome_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots)
        type_field[x, y] = BOT_CELLTYPE
        id_field[x, y] = bot_id
    else:
        print(f'could not spawn the bot {bot}. The position {x} {y} is occupied by entity type {type_field[x, y]}.')

    return bot_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots, type_field, id_field
@njit(cache=True)
def delete_bot(bot_id,
               bot_positions, bot_ages, bot_energies, bot_stack_top, bots,
               type_field, id_field):
    x, y = bot_positions[bot_id][0], bot_positions[bot_id][1]
    type_field[x, y] = AIR_CELLTYPE
    bot_positions, bot_ages, bot_energies, bot_stack_top, bots, id_field = pull_bot_stack(bot_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots, id_field)

    return bot_positions, bot_ages, bot_energies, bot_stack_top, bots, type_field, id_field
@njit(cache=True)
def push_organics_stack(organic_position, organic_energy, organics_positions, organics_energies, organic_stack_top):
    organic_stack_top += 1
    if organic_stack_top >= WORLD_VOLUME:
        raise OverflowError('organic_stack overflow')
    organic_id = organic_stack_top
    organics_positions[organic_id] = organic_position
    organics_energies[organic_id] = organic_energy

    return organic_id, organics_positions, organics_energies, organic_stack_top
@njit(cache=True)
def pull_organics_stack(organic_id, organics_positions, organics_energies, organic_stack_top, id_field):
    if organic_id == organic_stack_top:
        organic_stack_top -= 1
    else:
        x, y = organics_positions[organic_stack_top][0], organics_positions[organic_stack_top][1]
        organics_positions[organic_id] = x, y
        id_field[x, y] = organic_id
        organics_energies[organic_id] = organics_energies[organic_stack_top]
        organic_stack_top -= 1

    return organics_positions, organics_energies, organic_stack_top, id_field
@njit(cache=True)
def spawn_organic(organic_position, organic_energy, organic_is_falling, organics_positions, organics_energies, organics_falling, organic_stack_top, type_field, id_field):
    x, y = organic_position[0], organic_position[1]
    if type_field[x, y] == AIR_CELLTYPE:
        organic_id, organics_positions, organics_energies, organic_stack_top = push_organics_stack(organic_position, organic_energy, organics_positions, organics_energies, organic_stack_top)
        organics_falling[organic_id] = organic_is_falling
        type_field[x, y] = ORGANIC_CELLTYPE
        id_field[x, y] = organic_id
    else:
        print(f'could not spawn the organic. The position {x} {y} is occupied by entity type {type_field[x, y]}.')

    return organic_id, organics_positions, organics_energies, organic_stack_top, type_field, id_field
@njit(cache=True)
def delete_organic(organic_id, organics_positions, organics_energies, organic_stack_top, type_field, id_field):
    x, y = organics_positions[organic_id][0], organics_positions[organic_id][0]
    organics_positions, organics_energies, organic_stack_top, id_field = pull_organics_stack(organic_id, organics_positions, organics_energies, organic_stack_top, id_field)
    type_field[x, y] = AIR_CELLTYPE

    return organics_positions, organics_energies, organic_stack_top, type_field, id_field
@njit(cache=True)
def generate_genome(true_genome_size, bot_genomes, bot_genomes_stack_top):
    bot_genomes_stack_top += 1
    genome_id = bot_genomes_stack_top
    bot_genomes[genome_id] = r.randint(0, 256, size=true_genome_size).astype(np.uint8)
    bot_genomes[genome_id][0] = 0 #set is active to 0
    bot_genomes[genome_id][5] = MAXAGE_MULT #set maxage multiplier to MAXAGE_MULT
    return genome_id, bot_genomes, bot_genomes_stack_top
    

@njit(cache=True)
def spawn_first_batch(type_field, id_field, free_indices,
                      bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, bots, 
                      first_batch_size, true_genome_size, worldsize, world_volume, start_energy):
    
    if first_batch_size > world_volume:
                raise Exception('There is no free space in the world for new bots to generate. Check if FIRST_BATCH_SIZE smaller than WORLD_VOLUME.')
    
    for i in range(first_batch_size):
        #generate genome
        bot_genome_id, bot_genomes, bot_genomes_stack_top = generate_genome(true_genome_size, bot_genomes, bot_genomes_stack_top)

        bot_colors = bot_genomes[bot_genome_id][1], bot_genomes[bot_genome_id][2], bot_genomes[bot_genome_id][3]

        bot = np.empty(1, dtype=bot_dtype)
        bot[0]['id'] = np.uint32(0)
        bot[0]['genome_id'] = np.uint32(bot_genome_id)
        bot[0]['instruction_id'] = np.uint16(0)
        bot[0]['reading_step'] = np.uint8(1)
        bot[0]['colorR'] = bot_colors[0]
        bot[0]['colorG'] = bot_colors[1]
        bot[0]['colorB'] = bot_colors[2]

        #get random position
        idx = free_indices[i]
        x = idx // worldsize[1]
        y = idx % worldsize[1]
        pos = (np.uint16(x), np.uint16(y))

        #spawn bot
        bot_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots, type_field, id_field = spawn_bot(bot, pos, 0, start_energy, bot_genome_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots, type_field, id_field)

    return type_field, id_field, free_indices, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, bots