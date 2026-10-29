import pygame as pg
from config import *

'''   BUTTONS   '''
def init_buttons():
    buttons_data = []
    #placeholder button
    placeholder_texture = pg.image.load('sprites/placeholder.png')
    placeholder_position = 0, 0
    placeholder_size = placeholder_texture.get_size()
    def placeholder_function(string):
        print(string)
    buttons_data.append(placeholder_texture)
    buttons_data.append(placeholder_position)
    buttons_data.append(placeholder_size)
    buttons_data.append(placeholder_function)
    #other buttons

    return buttons_data
'''   PUSH BUTTONS   '''
def init_push_buttons():
    push_buttons_data = []
    #placeholder push button
    placeholder_push_unpressed_texture = pg.image.load('sprites/placeholder_push_unpressed.png')
    placeholder_push_pressed_texture = pg.image.load('sprites/placeholder_push_pressed.png')
    placeholder_push_position = 0, 100
    placeholder_push_size = placeholder_push_pressed_texture.get_size()
    plaseholder_push_active = False
    def placeholder_push_function(string):
        print(string)
    def placeholder_pull_function(string):
        print(string)
    push_buttons_data.append(placeholder_push_unpressed_texture)
    push_buttons_data.append(placeholder_push_pressed_texture)
    push_buttons_data.append(placeholder_push_position )
    push_buttons_data.append(placeholder_push_size)
    push_buttons_data.append(plaseholder_push_active)
    push_buttons_data.append(placeholder_push_function)
    push_buttons_data.append(placeholder_pull_function)
    #placeholder checkbox
    placeholder_checkbox_off_texture = pg.image.load('sprites/placeholder_checkbox_off.png')
    placeholder_checkbox_on_texture = pg.image.load('sprites/placeholder_checkbox_on.png')
    placeholder_checkbox_position = 120, 100
    placeholder_checkbox_size = placeholder_push_pressed_texture.get_size()
    placeholder_checkbox_active = False
    def placeholder_checkbox_on_function(string):
        print(string)
    def placeholder_checkbox_off_function(string):
        print(string)
    push_buttons_data.append(placeholder_checkbox_off_texture)
    push_buttons_data.append(placeholder_checkbox_on_texture)
    push_buttons_data.append(placeholder_checkbox_position)
    push_buttons_data.append(placeholder_checkbox_size)
    push_buttons_data.append(placeholder_checkbox_active)
    push_buttons_data.append(placeholder_checkbox_on_function)
    push_buttons_data.append(placeholder_checkbox_off_function)
    
    return push_buttons_data

'''   SLIDERS   '''
def init_sliders():
    sliders_data = []
    #placeholder slider
    placeholder_slider_body_texture = pg.image.load('sprites/placeholder_slider_body.png')
    placeholder_slider_dot_texture = pg.image.load('sprites/placeholder_slider_dot.png')
    placeholder_slider_body_position = 0, 60
    placeholder_slider_body_size = placeholder_slider_body_texture.get_size()
    placeholder_slider_dot_position = 0, 60
    placeholder_slider_dot_size = placeholder_slider_dot_texture.get_size()
    placeholder_slider_active = False
    def placeholder_slider_function(placeholder_slider_dot_position):
        rgb_speed = placeholder_slider_dot_position[0]//10
        return rgb_speed
    sliders_data.append(placeholder_slider_body_texture)
    sliders_data.append(placeholder_slider_dot_texture)
    sliders_data.append(placeholder_slider_body_position)
    sliders_data.append(placeholder_slider_body_size)
    sliders_data.append(placeholder_slider_dot_position)
    sliders_data.append(placeholder_slider_dot_size)
    sliders_data.append(placeholder_slider_function)
    sliders_data.append(placeholder_slider_active)
    #other sliders

    return sliders_data

'''   POPUP WINDOWS   '''
def init_popup_windows(ui_surface, TEXT_BIGFONT, TEXT_MIDFONT, TEXT_SMALLFONT):
    popup_windows_data = []
    #placeholder popup window
    placeholder_popup_window_bg_texture = pg.image.load('sprites/placeholder_popup_window_bg.png')
    placeholder_popup_window_button_down_texture = pg.image.load('sprites/placeholder_popup_window_button_down.png')
    placeholder_popup_window_button_up_texture = pg.image.load('sprites/placeholder_popup_window_button_up.png')
    placeholder_popup_window_button_position = 0, 80
    placeholder_popup_window_button_size = placeholder_popup_window_button_down_texture.get_size()
    placeholder_popup_window_active = False
    #popup contents
    def handle_contents_placeholder_popup_window(window_bg, TEXT_SMALLFONT):
        TEST_TEXT = TEXT_SMALLFONT.render('test', False, 'Black')
        window_bg.blit(TEST_TEXT, (10,5))
    popup_windows_data.append(placeholder_popup_window_bg_texture)
    popup_windows_data.append(placeholder_popup_window_button_down_texture)
    popup_windows_data.append(placeholder_popup_window_button_up_texture)
    popup_windows_data.append(placeholder_popup_window_button_position)
    popup_windows_data.append(placeholder_popup_window_button_size)
    popup_windows_data.append(placeholder_popup_window_active)
    popup_windows_data.append(handle_contents_placeholder_popup_window)

    return popup_windows_data

popup_active = False
#button handler
def button_handler(popup_active, onclick_function, function_arguments, button_texture:pg.image, button_position:tuple, button_size:tuple, ui_surface:pg.Surface, click_pos:tuple, ui_position:tuple):
    #draw sprite
    ui_surface.blit(button_texture, button_position)
    #handle click
    if click_pos != None and not popup_active:
        button_global_position = button_position[0] + ui_position[0], button_position[1] + ui_position[1]
        button_corner = button_size[0] + button_global_position[0], button_size[1] + button_global_position[1]
        button_clicked_x = click_pos[0] >= button_global_position[0] and click_pos[0] <= button_corner[0]
        button_clicked_y = click_pos[1] >= button_global_position[1] and click_pos[1] <= button_corner[1]
        button_clicked = button_clicked_x and button_clicked_y

        if button_clicked:
            onclick_function(function_arguments)
#push button handler
def push_button_handler(popup_active, button_unpressed_texture:pg.image, button_pressed_texture:pg.image, button_position:tuple, button_size:tuple, button_active, onpush_function, onpull_function, onpush_function_arguments, onpull_function_arguments, ui_surface:pg.Surface, click_pos:tuple, ui_position:tuple):
    #draw sprite
    #handle click
    if button_active:
        ui_surface.blit(button_pressed_texture, button_position)
        if click_pos != None and not popup_active:
            button_global_position = button_position[0] + ui_position[0], button_position[1] + ui_position[1]
            button_corner = button_size[0] + button_global_position[0], button_size[1] + button_global_position[1]
            button_clicked_x = click_pos[0] >= button_global_position[0] and click_pos[0] <= button_corner[0]
            button_clicked_y = click_pos[1] >= button_global_position[1] and click_pos[1] <= button_corner[1]
            button_clicked = button_clicked_x and button_clicked_y

            if button_clicked:
                onpush_function(onpull_function_arguments)
                button_active = False
    else:
        ui_surface.blit(button_unpressed_texture, button_position)
        if click_pos != None and not popup_active:
            button_global_position = button_position[0] + ui_position[0], button_position[1] + ui_position[1]
            button_corner = button_size[0] + button_global_position[0], button_size[1] + button_global_position[1]
            button_clicked_x = click_pos[0] >= button_global_position[0] and click_pos[0] <= button_corner[0]
            button_clicked_y = click_pos[1] >= button_global_position[1] and click_pos[1] <= button_corner[1]
            button_clicked = button_clicked_x and button_clicked_y

            if button_clicked:
                onpull_function(onpush_function_arguments)
                button_active = True
    return button_active

#slider handler
def slider_handler(popup_active, slider_function, function_arguments, slider_body_texture, slider_dot_texture, slider_body_position, slider_body_size, slider_dot_position, slider_dot_size, ui_surface, click_pos, release_pos, slider_active, ui_position):
    #handle slider
    if click_pos != None and not popup_active:
        slider_dot_global_position = slider_dot_position[0] + ui_position[0], slider_dot_position[1] + ui_position[1]
        slider_dot_corner = slider_dot_size[0] + slider_dot_global_position[0], slider_dot_size[1] + slider_dot_global_position[1]

        dot_clicked_x = click_pos[0] >= slider_dot_global_position[0] and click_pos[0] <= slider_dot_corner[0]
        dot_clicked_y = click_pos[1] >= slider_dot_global_position[1] and click_pos[1] <= slider_dot_corner[1]
        dot_clicked = dot_clicked_x and dot_clicked_y
        if dot_clicked:
            slider_active = True
    function_output = None
    if slider_active:
        mouse_pos = pg.mouse.get_pos()

        slider_body_global_position_x = slider_body_position[0] + ui_position[0]
        slider_body_corner_x = slider_body_size[0] + slider_body_global_position_x

        mouse_in_range = mouse_pos[0] >= slider_body_global_position_x and mouse_pos[0] <= slider_body_corner_x
        if mouse_in_range:
            slider_dot_position = mouse_pos[0] - slider_body_global_position_x - slider_dot_size[0]/2, slider_dot_position[1]
        else:
            mouse_to_the_rigt = mouse_pos[0] < slider_body_global_position_x
            if mouse_to_the_rigt:
                slider_dot_position = slider_body_position[0], slider_dot_position[1]
            else:
                slider_dot_position = slider_body_position[0] + slider_body_size[0] - slider_dot_size[0], slider_dot_position[1]

        if release_pos != None:
            function_output = slider_function(function_arguments)
            slider_active = False
    #draw slider
    ui_surface.blit(slider_body_texture, slider_body_position)
    ui_surface.blit(slider_dot_texture, slider_dot_position)

    return slider_dot_position, slider_active, function_output
#popup window handler
def popup_window_handler(any_popup_active, bg_texture, button_down_texture, button_up_texture, button_position, button_size, this_popup_active, function, function_arguments, ui_surface, click_pos, ui_position):
    if not this_popup_active:
        #draw button
        ui_surface.blit(button_down_texture, button_position)
        #handle click
        if click_pos != None:
            button_global_position = button_position[0] + ui_position[0], button_position[1] + ui_position[1]
            button_corner = button_size[0] + button_global_position[0], button_size[1] + button_global_position[1]
            button_clicked_x = click_pos[0] >= button_global_position[0] and click_pos[0] <= button_corner[0]
            button_clicked_y = click_pos[1] >= button_global_position[1] and click_pos[1] <= button_corner[1]
            button_clicked = button_clicked_x and button_clicked_y

            if button_clicked:
                this_popup_active = True
    else:
        #draw window
        ui_surface.blit(button_up_texture, button_position)
        bg_position = button_position[0], button_position[1] + button_size[1]
        function(bg_texture, function_arguments)
        ui_surface.blit(bg_texture, bg_position)
        #handle click
        if click_pos != None:
            button_global_position = button_position[0] + ui_position[0], button_position[1] + ui_position[1]
            button_corner = button_size[0] + button_global_position[0], button_size[1] + button_global_position[1]
            button_clicked_x = click_pos[0] >= button_global_position[0] and click_pos[0] <= button_corner[0]
            button_clicked_y = click_pos[1] >= button_global_position[1] and click_pos[1] <= button_corner[1]
            button_clicked = button_clicked_x and button_clicked_y

            if button_clicked:
                this_popup_active = False
    return this_popup_active

#ui handler
def handle_ui(GLOBAL_COUNTER, TEXT_BIGFONT, TEXT_MIDFONT, TEXT_SMALLFONT, main_surface, ui_surface, UISIZE, UIPOSITION, click_pos, release_pos, buttons_data, sliders_data, popup_active, popup_windows_data, push_buttons_data):
    ui_surface.fill((100,100,100))
    #buttons
    placeholder_texture, placeholder_position, placeholder_size, placeholder_function = buttons_data[:4]
    button_handler(popup_active, placeholder_function, 'yes123', placeholder_texture, placeholder_position, placeholder_size, ui_surface, click_pos, UIPOSITION)
    #sliders
    placeholder_slider_body_texture, placeholder_slider_dot_texture, placeholder_slider_body_position, placeholder_slider_body_size, placeholder_slider_dot_position, placeholder_slider_dot_size, placeholder_slider_function, placeholder_slider_active = sliders_data[:8]
    placeholder_slider_dot_position, placeholder_slider_active, RGB_SPEED = slider_handler(popup_active, placeholder_slider_function, placeholder_slider_dot_position, placeholder_slider_body_texture, placeholder_slider_dot_texture, placeholder_slider_body_position, placeholder_slider_body_size, placeholder_slider_dot_position, placeholder_slider_dot_size, ui_surface, click_pos, release_pos, placeholder_slider_active, UIPOSITION)
    sliders_data[4] = placeholder_slider_dot_position
    sliders_data[7] = placeholder_slider_active
    #push buttons
    placeholder_push_unpressed_texture, placeholder_push_pressed_texture, placeholder_push_position, placeholder_push_size, plaseholder_push_active, placeholder_push_function, placeholder_pull_function = push_buttons_data[:7]
    push_buttons_data[4] = push_button_handler(popup_active, placeholder_push_unpressed_texture, placeholder_push_pressed_texture, placeholder_push_position, placeholder_push_size, plaseholder_push_active, placeholder_push_function, placeholder_pull_function, 'on', 'off', ui_surface, click_pos, UIPOSITION)
    placeholder_checkbox_off_texture, placeholder_checkbox_on_texture, placeholder_checkbox_position, placeholder_checkbox_size, placeholder_checkbox_active, placeholder_checkbox_on_function, placeholder_checkbox_off_function = push_buttons_data[7:15]
    push_buttons_data[11] = push_button_handler(popup_active, placeholder_checkbox_off_texture, placeholder_checkbox_on_texture, placeholder_checkbox_position, placeholder_checkbox_size, placeholder_checkbox_active, placeholder_checkbox_on_function, placeholder_checkbox_off_function, 'check', 'uncheck', ui_surface, click_pos, UIPOSITION)
    #popup windows (should always be handled LAST)
    placeholder_popup_window_bg_texture, placeholder_popup_window_button_down_texture, placeholder_popup_window_button_up_texture, placeholder_popup_window_button_position, placeholder_popup_window_button_size, placeholder_popup_window_active, handle_contents_placeholder_popup_window = popup_windows_data[:7]
    placeholder_popup_window_active = popup_window_handler(popup_active, placeholder_popup_window_bg_texture, placeholder_popup_window_button_down_texture, placeholder_popup_window_button_up_texture, placeholder_popup_window_button_position, placeholder_popup_window_button_size, placeholder_popup_window_active, handle_contents_placeholder_popup_window, TEXT_SMALLFONT, ui_surface, click_pos, UIPOSITION)
    popup_windows_data[5] = placeholder_popup_window_active
    #see if atleast one popup is active
    all_active_popups = popup_windows_data[5::7]
    atleast_one_popup_active = False
    for i in all_active_popups:
        atleast_one_popup_active = atleast_one_popup_active or i
    popup_active = atleast_one_popup_active

    
    global_counter_ui1 = TEXT_BIGFONT.render('frames:'+str(GLOBAL_COUNTER), False, 'Black')
    global_counter_ui2 = TEXT_MIDFONT.render('frames:'+str(GLOBAL_COUNTER), False, 'Black')
    global_counter_ui3 = TEXT_SMALLFONT.render('frames:'+str(GLOBAL_COUNTER), False, 'Black')
    ui_surface.blit(global_counter_ui1, (120, 0))
    ui_surface.blit(global_counter_ui2, (120, 30))
    ui_surface.blit(global_counter_ui3, (120, 60))

    main_surface.blit(ui_surface, UIPOSITION)

    return RGB_SPEED, popup_active