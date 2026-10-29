'''=============================================     PARAMS     ============================================'''
#graphics
SCREENSIZE = 1200, 700
WORLDSIZE = 100, 100
SIMULATION_WINDOW_POSITION = 10, 10
SIMULATION_WINDOW_SIZE = 500, 500
UI_WINDOW_SIZE = 300, 700
UI_WINDOW_POSITION = 900, 0
BIG_FONTSIZE = 32
MID_FONTSIZE = 24
SMALL_FONTSIZE = 14
MAX_FPS = 60
BG_COLOR = 100, 100, 100  #color of the background of the simulation window
UI_BG_COLOR = 100, 100, 100 #color of the background of the ui surface
GLOBAL_COUNTER = 0 #tick counter from the start of the program
#simulation settings
RANDOMIZE_SEED = True
SEED = 0 #only does something if RANDOMIZE_SEED = False
GENOME_SIZE = 50 #maximum genome size that any bot can have
FIRST_BATCH_SIZE = 100 #how much bots to spawn every time the simulation restarts
MAXAGE_MULT = 1 #roughly how long first bots can live. 1 is about 4 seconds max or 256 frames
MAX_ENERGY = 30000 #maximum energy a bot can have
MIN_ENERGY = 200 #if a bot has less than this, it dies (do not set this smaller than energy_los, you need a buffer so it doesnt overflows when goes negative)
START_ENERGY = MIN_ENERGY + 100 #how much energy to give to first bots every time the simulation restarts
ENERGY_LOS = 1 #how much energy a bot loses every turn
ORGANIC_SETTLEMENT_TIME = 60 #how long organics will wait until frozen in frames
ORGANIC_COLOR = 100, 100, 100

'''=============================================     CONSTANTS     ============================================='''
TRUE_GENOME_SIZE = GENOME_SIZE*2 + 4 + 2 #is active + bot color + maxage + maxage_mult + genome size + instruction parameters
GENOME_RESERVED_IDX = 6 #indicies reserved for smth like is active, color etc.
WORLD_VOLUME = WORLDSIZE[0]*WORLDSIZE[1] #how much space is in this world
#cell types
AIR_CELLTYPE = 0
BOT_CELLTYPE = 1
ORGANIC_CELLTYPE = 2
#backgrounds
RGB_DEFFAULT_SPEED = 2
RGB_DEFFAULT_BRIGHTNESS = 20

#genome instructions
PHOTOSYNTESIS_INSTR = 0, 1, 2, 3
MOVE_INSTR = 4, 5, 6, 7
DIVIDE_INSTR = 8, 9, 10, 11
ATTACK_INSTR = 12, 13, 14, 15