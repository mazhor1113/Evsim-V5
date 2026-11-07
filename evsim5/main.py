from graphics.backend.PyGame_backend import PygameBackend
from graphics.ui import manager, widgets
from graphics.assets import load_textures
from graphics.event import EventType

import graphics.canvas as Canvas
import config.application as app_config

'''   INIT   '''
backend = PygameBackend()
manager = manager.UIManager()

load_textures(backend)

canvas = Canvas.Canvas()

simulationViewport = widgets.SimulationViewport(
    canvas = canvas,
    viewport_position = (10, 10),
    )


#create ui elements
fps_counter = widgets.Text(
    rect = widgets.Rect(5, 0, 120, 20),
    text=lambda: f"FPS: {backend.clock.get_fps():.0f}",
    color=(0, 0, 0),
)

manager.add(simulationViewport)
manager.add(fps_counter)

'''   MAIN CYCLE   '''
running = True
while running:

    #event handling
    events = backend.get_events()
    for event in events:
        manager.handle_event(event)
        if event.type == EventType.QUIT:
            running = False

    #end operations
    backend.fill_surface("ui_surface", app_config.ui_bg_color)

    manager.draw_all(backend)

    backend.compose_surfaces()

    manager.draw_screen_elements(backend)

    backend.present()
    
backend.quit()