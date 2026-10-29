from config import *
import numpy as np
from numpy import random as r
from typing import Annotated
import numpy.typing as npt
from numba import njit
from numba import from_dtype
import simulation.utils as u

bot_dtype = np.dtype([
    ('id', np.uint32),
    ('genome_id', np.uint32),
    ('instruction_id', np.uint16),
    ('reading_step', np.uint8),
    ('colorR', np.uint8),
    ('colorG', np.uint8),
    ('colorB', np.uint8)
])
action_queue_dtype = np.dtype([
    ('bot_id', np.uint32),
    ('instruction', np.uint8),
    ('parameter', np.uint8),
    ('action_cord_x', np.int16),
    ('action_cord_y', np.int16)
])
def init_engine(worldsize, world_volume, true_genome_size):
    '''INIT WORLD'''
    type_field = np.zeros(worldsize, dtype = np.uint8)
    id_field = np.zeros(worldsize, dtype = np.uint32)

    '''INIT BOTS'''
    free_indices = np.arange(WORLD_VOLUME, dtype=np.int32)
    r.shuffle(free_indices)

    max_entities = world_volume
    bot_positions = np.zeros((max_entities, 2), dtype = np.int16)
    bot_positions.fill(-1)
    bot_ages = np.zeros(max_entities, dtype = np.uint32)
    bot_energies = np.zeros(max_entities, dtype = np.uint16)
    bot_genomes = np.zeros((max_entities, true_genome_size), dtype = np.uint8)
    bot_stack_top = -1
    bot_genomes_stack_top = -1

    action_queue = np.zeros(max_entities, dtype = action_queue_dtype)

    bots = np.zeros(max_entities, dtype = bot_dtype)

    '''INIT ORGANICS'''
    organics_positions = np.zeros((max_entities, 2), dtype = np.int16)
    organics_positions.fill(-1)
    organics_energies = np.zeros(max_entities, dtype = np.uint16)
    organics_falling = np.zeros(max_entities, dtype = np.bool)
    organics_wait_times = np.zeros(max_entities, dtype = np.uint8)
    organics_stack_top = -1


    return type_field, id_field, free_indices, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_falling, organics_wait_times, organics_stack_top


@njit(cache=True)
def process_bot_genomes_and_shit_idk(type_field, id_field, canvas,
                                     bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots,
                                     organics_positions, organics_energies, organics_falling, organics_stack_top):
    bot_id = 0
    while bot_id <= bot_stack_top:
        bot = bots[bot_id]
        genome_id = bot['genome_id']
        instruction_id = bot['instruction_id']
        reading_step = bot['reading_step']
        colorR = bot['colorR']
        colorG = bot['colorG']
        colorB = bot['colorB']

        pos = bot_positions[bot_id][0], bot_positions[bot_id][1]
        age = bot_ages[bot_id]
        energy = bot_energies[bot_id]
        genome_full = bot_genomes[genome_id]
        genome = genome_full[GENOME_RESERVED_IDX:]
        maxage = genome_full[4] * genome_full[5]

        bot_is_about_to_die = energy <= MIN_ENERGY or age >= maxage
        if not bot_is_about_to_die:
            canvas[pos[0]][pos[1]][0] = colorR
            canvas[pos[0]][pos[1]][1] = colorG
            canvas[pos[0]][pos[1]][2] = colorB

            bot_id += 1
        else:
            #delete bot
            bot_positions, bot_ages, bot_energies, bot_stack_top, bots, type_field, id_field = u.delete_bot(bot_id, bot_positions, bot_ages, bot_energies, bot_stack_top, bots, type_field, id_field)
            #spawn  organic
            organic_id, organics_positions, organics_energies, organics_stack_top, type_field, id_field = u.spawn_organic(pos, energy, True, organics_positions, organics_energies, organics_falling, organics_stack_top, type_field, id_field)
    return type_field, id_field, canvas, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_stack_top
@njit(cache=True)
def process_organics(type_field, id_field, canvas, organics_positions, organics_falling, organics_wait_times, organics_stack_top, ORGANIC_COLOR):
    organic_id = 0
    while organic_id <= organics_stack_top:
        x, y = organics_positions[organic_id][0], organics_positions[organic_id][1]
        is_falling = organics_falling[organic_id]
        wait_time = organics_wait_times[organic_id]

        if is_falling:
            cell_type_under = type_field[x, y+1]
            if not cell_type_under == AIR_CELLTYPE:
                checkposes = np.array([-1, 1], dtype=np.int64)
                r.shuffle(checkposes)
                space_avialable = False
                checkpos1 = type_field[x + checkposes[0], y+1]
                checkpos2 = type_field[x + checkposes[1], y+1]
                if checkpos1 == AIR_CELLTYPE:
                    space_avialable = True
                    free_x = x + checkposes[0]
                elif checkpos2 == AIR_CELLTYPE:
                    space_avialable = True
                    free_x = x + checkposes[1]
            else:
                space_avialable = True
            if space_avialable:
                type_field[x, y] = AIR_CELLTYPE
                id_field[x, y] = AIR_CELLTYPE
                y += 1
                type_field[free_x, y] = ORGANIC_CELLTYPE
                id_field[free_x, y] = organic_id
                organics_positions[organic_id] = free_x, y
            else:
                wait_time += 1
                organics_wait_times[organic_id] = wait_time
                if wait_time >= ORGANIC_SETTLEMENT_TIME:
                    organics_falling[organic_id] = False

        organic_id += 1
        canvas[x, y, 0] = ORGANIC_COLOR[0]
        canvas[x, y, 1] = ORGANIC_COLOR[1]
        canvas[x, y, 2] = ORGANIC_COLOR[2]
    return type_field, id_field, canvas, organics_positions, organics_falling, organics_wait_times, organics_stack_top


@njit(cache=True)
def process_action_queue_and_bots_ig(type_field, id_field,
                                     bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots,
                                     organics_positions, organics_energies, organics_stack_top):
    bot_ages += np.uint32(1)
    bot_energies -= np.uint16(ENERGY_LOS)

    return type_field, id_field, bot_positions, bot_ages, bot_energies, bot_genomes, bot_stack_top, bot_genomes_stack_top, action_queue, bots, organics_positions, organics_energies, organics_stack_top