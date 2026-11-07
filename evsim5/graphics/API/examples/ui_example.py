from graphics.backend.PyGame_backend import PygameBackend
from graphics.ui import manager, widgets
import graphics.assets as assets
from graphics.event import EventType
from graphics.canvas import Canvas
import config.config as config

'''   INIT   '''
backend = PygameBackend()
manager = manager.UIManager()

assets.load_textures(backend)

'''   CREATING UI ELEMENTS   '''
#ui functions
def button_click():
    print("button works")

def push_change(toggled):
    if toggled:
        print("on")
    else:
        print("off")

def slider(value):
    print(value)

#window children functions
def window_child_button_func():
    print("child works")

def window_child_toggle_func(toggled):
    if toggled:
        print("child on")
    else:
        print("child off")

def window_child_slider_func(value):
    print(f"child: {value}")

mult = 60 #just spacing for easy redacting

#create ui elements
fps_counter = widgets.Text(
    rect = widgets.Rect(5, 0, 120, 20),
    text=lambda: f"FPS: {backend.clock.get_fps():.0f}",
    color=(0, 0, 0),
)
button = widgets.Button(
    x = 5,
    y = mult * 1,
    texture_key = "placeholder_button", 
    on_click = button_click, 
    pressed_texture_key = "placeholder_button_pressed",
    backend = backend,
    )
toggle_button = widgets.ToggleButton(
    x = 5,
    y = mult * 2,
    texture_off_key = "placeholder_toggle_button_off", 
    texture_on_key = "placeholder_toggle_button_on", 
    on_change = push_change,
    backend = backend,
    )
slider = widgets.Slider(
    x = 5,
    y = mult * 3,
    body_texture_key = "placeholder_slider_body", 
    thumb_texture_key = "placeholder_slider_thumb", 
    on_change = slider,
    backend = backend,
    )
text = widgets.Text(
    rect = widgets.Rect(5, mult * 4, 120, 40), 
    text = "aboba", 
    font_key = "font_big", 
    color = (255, 0, 0),
    )
window = widgets.PopupWindow(
    rect = widgets.Rect(925, 35, 245, 300),
    title = "TEST",
    modal = False,
    visible = False,
)
window_opener = widgets.Button(
    x = 5,
    y = mult * 5,
    on_click = window.open,
    backend = backend,
)
modal_window = widgets.PopupWindow(
    rect = widgets.Rect(600, 350, 245, 300),
    title = "test warning",
    title_color = (255, 0, 0),
    modal = True,
    visible = False,
)
modal_window_opener = widgets.Button(
    x = 5,
    y = mult * 6,
    on_click = modal_window.open,
    backend = backend,
)
#window children
window_child_button = widgets.Button(
    x = 0,
    y = 0,
    on_click = window_child_button_func,
    backend = backend,
)
window_child_toggle = widgets.ToggleButton(
    x = 0,
    y = mult,
    on_change = window_child_toggle_func,
    backend = backend,
)
window_child_slider = widgets.Slider(
    x = 0,
    y = mult * 2,
    on_change = window_child_slider_func,
    backend = backend,
)
window_text = widgets.Text(
    rect = widgets.Rect(50, 1500, 100, 20),
    text = "fgh",
    color = (0, 255, 0),
)
#panel 1
panel1 = widgets.Panel(
    rect = widgets.Rect(5, 345, 180, 90),
)
panel1_opener = widgets.Button(
    x = 5,
    y = 345 - mult,
    on_click = panel1.open,
    backend = backend,
)
panel1_closer = widgets.Button(
    x = 160,
    y = 0,
    texture_key = "placeholder_window_hide",
    on_click = panel1.close,
    backend = backend,
)
panel1_resizer = widgets.Button(
    rect = widgets.Rect(0, 0, 100, 10),
)
#panel 2
panel2 = widgets.Panel(
    rect = widgets.Rect(5, 450 + mult, 180, 90),
)
panel2_opener = widgets.Button(
    x = 5,
    y = 450,
    on_click = panel2.open,
    backend = backend,
)
panel2_closer = widgets.Button(
    x = 160,
    y = 0,
    texture_key = "placeholder_window_hide",
    on_click = panel2.close,
    backend = backend,
)
panel2_resizer = widgets.Button(
    rect = widgets.Rect(0, 0, 10, 100),
)
#panel 3
panel3 = widgets.Panel(
    rect = widgets.Rect(5, 620 + mult, 180, 90),
)
panel3_opener = widgets.Button(
    x = 5,
    y = 620,
    on_click = panel3.open,
    backend = backend,
)
panel3_closer = widgets.Button(
    x = 160,
    y = 0,
    texture_key = "placeholder_window_hide",
    on_click = panel3.close,
    backend = backend,
)
panel3_resizer = widgets.Button(
    rect = widgets.Rect(0, 0, 20, 20),
)


#add children to the window (and panel)
window.add(window_child_button)
window.add(window_child_toggle)
window.add(window_child_slider)
window.add(window_text)
#panel 1
window.add(panel1)
window.add(panel1_opener)
panel1.add(panel1_closer)
panel1.add(fps_counter)
panel1.add_resize_handle(
    button = panel1_resizer,
    directions = ('top',),
    anchor = 'top',
    stretch = True,
)
#panel 2
window.add(panel2)
window.add(panel2_opener)
panel2.add(panel2_closer)
panel2.add(fps_counter)
panel2.add_resize_handle(
    button = panel2_resizer,
    directions = ('right',),
    anchor = 'right',
    stretch = False,
)
#panel 3
window.add(panel3)
window.add(panel3_opener)
panel3.add(panel3_closer)
panel3.add(fps_counter)
panel3.add_resize_handle(
    button = panel3_resizer,
    directions = ('bottom','right'),
    anchor = 'bottom-right',
    stretch = False,
)
#creating viewport
canvas = Canvas()
simulationViewport = widgets.SimulationViewport(canvas)

activate_pixel_selection = widgets.Button(
    rect = widgets.Rect(5, mult * 7, 50, 50),
    on_click = simulationViewport.activate_pixel_selection,
)
activate_area_selection = widgets.Button(
    rect = widgets.Rect(5, mult * 8, 50, 50),
    on_click = simulationViewport.activate_area_selection,
)

selected_pixel = widgets.Text(
    rect = widgets.Rect(5, mult * 9, 120, 20),
    font_key="font_small",
    text=lambda: f"selected pixel: {simulationViewport.selected_pixel_position}",
)
selected_area_text = widgets.Text(
    rect = widgets.Rect(5, mult * 9 + 20, 120, 20),
    font_key = "font_small",
    text = "selected area:",
)
selected_area = widgets.Text(
    rect = widgets.Rect(5, mult * 9 + 40, 120, 20),
    font_key="font_small",
    text=lambda: f"{simulationViewport.selected_rect}",
)

#register ui elements to the manager
manager.add(activate_pixel_selection)
manager.add(activate_area_selection)
manager.add(simulationViewport)
manager.add(selected_pixel)
manager.add(selected_area)
manager.add(selected_area_text)

manager.add(fps_counter)
manager.add(button)
manager.add(toggle_button)
manager.add(slider)
manager.add(text)
manager.add(window_opener)
manager.add(window)
manager.add(modal_window_opener)
manager.add(modal_window)



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
    backend.fill_surface("ui_surface", config.UI_BG_COLOR)

    manager.draw_all(backend)

    backend.compose_surfaces()

    manager.draw_screen_elements(backend)

    backend.present()
    
backend.quit()