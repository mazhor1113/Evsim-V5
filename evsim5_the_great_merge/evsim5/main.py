'''=============================================     INIT     ============================================='''
from config import *
from drawer import init_drawer, draw
import drawer
import pygame as pg
from numpy import random as r
import simulation.utils as utils
import simulation.engine as engine
import ui

#init drawer
pixelsize, main_surface, canvas_surface, ui_surface, canvas, CLOCK, TEXT_BIGFONT, TEXT_MIDFONT, TEXT_SMALLFONT = init_drawer(WORLDSIZE, SCREENSIZE, SIMULATION_WINDOW_SIZE, BIG_FONTSIZE, MID_FONTSIZE, SMALL_FONTSIZE, UISIZE)
#init engine
type_field, id_field, free_indices, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_falling, organics_wait_times, organics_stack_top = engine.init_engine(WORLDSIZE, WORLD_VOLUME, TRUE_GENOME_SIZE)
#init rng
SEED = utils.init_rng(RANDOMIZE_SEED, SEED)
#init ui
buttons_data = ui.init_buttons()
sliders_data = ui.init_sliders()
popup_windows_data = ui.init_popup_windows(ui_surface, TEXT_BIGFONT, TEXT_MIDFONT, TEXT_SMALLFONT)
popup_active = ui.popup_active
push_buttons_data = ui.init_push_buttons()


'''=============================================     MAIN CYCLE     ============================================='''
type_field, id_field, free_indices, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, bots = utils.spawn_first_batch(type_field, id_field, free_indices, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, bots, FIRST_BATCH_SIZE, TRUE_GENOME_SIZE, WORLDSIZE, WORLD_VOLUME, START_ENERGY)
RGB_SPEED = RGB_DEFFAULT_SPEED

while True:
    utils.DO_CYCLE_START(canvas, BG_COLOR)
    ###   BODY   ###
    #rgb bg
    BG_COLOR = utils.rgb_bg_calc(GLOBAL_COUNTER, RGB_SPEED, RGB_DEFFAULT_BRIGHTNESS)
    #organic color
    ORGANIC_COLOR = (100 + 2*GLOBAL_COUNTER)%255, (100 + 2*GLOBAL_COUNTER)%255, (100 + 2*GLOBAL_COUNTER)%255
    #process_bots
    type_field, id_field, canvas, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_stack_top = engine.process_bot_genomes_and_shit_idk(type_field, id_field, canvas, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_falling, organics_stack_top)
    type_field, id_field, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_stack_top = engine.process_action_queue_and_bots_ig(type_field, id_field, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_stack_top)
    #process organics
    type_field, id_field, canvas, organics_positions, organics_falling, organics_wait_times, organics_stack_top = engine.process_organics(type_field, id_field, canvas, organics_positions, organics_falling, organics_wait_times, organics_stack_top, ORGANIC_COLOR)
    ###   DEBUG   ###
    #canvas = drawer.__DEBUG__PROJECT_FIELD_TO_CANVAS(WORLDSIZE, type_field, canvas, BOT_CELLTYPE, ORGANIC_CELLTYPE, AIR_CELLTYPE)
    
    ################
    GLOBAL_COUNTER, RGB_SPEED_OUT, SCREENSIZE, clickpos, popup_active = utils.DO_CYCLE_END(popup_active, GLOBAL_COUNTER, MAX_FPS, CLOCK, SIMULATION_WINDOW_POSITION, pixelsize, main_surface, canvas_surface, ui_surface, buttons_data, sliders_data, popup_windows_data, push_buttons_data, UISIZE, UIPOSITION, canvas, TEXT_BIGFONT, TEXT_MIDFONT, TEXT_SMALLFONT)
    
    if RGB_SPEED_OUT != None:
        RGB_SPEED = RGB_SPEED_OUT