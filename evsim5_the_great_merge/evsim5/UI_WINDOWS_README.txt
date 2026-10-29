EVSim UI containers: usage notes
================================

Coordinate rules
----------------
- Ordinary root UI element rects use ui_surface-local coordinates.
- Independent root PopupWindow rects use full-screen coordinates and are drawn to main_surface.
- Popup root coordinates are not shifted by UI_WINDOW_POSITION. For example, a popup at (925, 35) is positioned 25 pixels inside a UI panel whose screen origin is (900, 0).
- Panel children use coordinates relative to the panel's top-left corner.
- PopupWindow children use coordinates relative to the content area below the title bar.
- A PopupWindow nested inside another container follows its parent's coordinate system; independent popup windows should be registered as root elements with manager.add(popup).
- UIManager.handle_event() receives unmodified screen-coordinate UIEvent objects. It transforms coordinates only when routing to ordinary ui_surface elements.
- handle_event() returns True when the UI consumes or intentionally blocks an event, and False when another subsystem (e.g. simulation/debug tools) may process it.

PopupWindow
-----------
- Close and minimize/collapse controls are created automatically.
- The vertical scrollbar is created automatically when direct child content exceeds the viewport.
- Mouse-wheel scrolling and the scrollbar both change scroll_y.
- The window can be moved by dragging its title bar and resized from its bottom-right corner.
- modal=True causes UIManager to route input only inside the topmost active modal window and block click-through outside it.
- Keep a hidden popup in the UI tree (manager.add(popup), or parent.add(popup)) before opening it.
- For an independent popup, register it once with manager.add(popup), even while hidden.
- Only after registration, create an opener with manager.make_open_button(popup, rect, texture_key) and add the returned Button to the owner. The helper raises immediately if the popup was not registered.
- Clicking that opener calls manager.open_window(), sets visible=True and raises the popup in root z-order. The popup is independent of the window containing its opener.

Panel
-----
- Panel is a lightweight child container and has no built-in close/minimize controls.
- Its children are clipped to the panel by default. Set clip_children=False if child drawing may extend beyond the panel.
- Set scrollable=True for wheel scrolling; unlike PopupWindow, Panel does not create an automatic scrollbar.

Backend contract
----------------
GraphicsBackend requires get_clip(surface_key) and set_clip(surface_key, rect).
PygameBackend implements these with Surface.get_clip/set_clip. UIManager restores the
previous clip after drawing each surface. Texture drawing scales textures to Rect dimensions
and caches scaled versions to avoid repeating transforms every frame.

Frame order
-----------
1. Draw ordinary UI to ui_surface with manager.draw_all(backend).
2. Composite the simulation and UI surfaces onto main_surface with backend.compose_surfaces().
3. Draw independent screen roots with manager.draw_screen_elements(backend).
4. Present the completed main_surface with backend.present().

Event routing
-------------
Call manager.handle_event(event) for every backend event. If it returns False, the event
may be passed to simulation/debug input handling. Global QUIT and RESIZE events are not
consumed by UIManager. Mouse capture remains active while dragging outside an element.

Run the headless logic smoke test from the project root:
    python -m testing_sandbox.ui_testing.window_logic_test

Run the graphical demonstration (requires pygame) from the project root:
    python -m testing_sandbox.ui_testing.window_test
