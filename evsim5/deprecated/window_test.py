"""Standalone manual test for nested panels and popup windows.

Run from the evsim5 project root:
    python -m testing_sandbox.ui_testing.window_test
"""
from graphics.backend.PyGame_backend import PygameBackend
from graphics.assets import load_textures
from graphics.event import EventType
from graphics.ui.manager import UIManager
from graphics.ui.widgets import Button, Panel, PopupWindow, Rect, Text

backend = PygameBackend()
manager = UIManager()
load_textures(backend)

# PopupWindow creates its own close/minimize controls and its scrollbar automatically.
settings = PopupWindow(
    # Popup root rect is in screen coordinates (independent of ui_surface).
    rect=Rect(925, 35, 245, 300),
    title="Settings",
    modal=False,
    visible=False,
)
settings.add(Text(Rect(8, 8, 180, 22), "This content scrolls"))
for i in range(12):
    settings.add(Text(Rect(8, 38 + i * 24, 170, 20), f"Setting {i + 1}"))

# A real nested panel: it moves and clips together with its parent window.
inner_panel = Panel(
    rect=Rect(8, 345, 180, 90),
    children=[Text(Rect(8, 8, 160, 20), "Nested panel")],
)
settings.add(inner_panel)

# The opener belongs to the parent/root UI, not to the hidden popup itself.
manager.add(settings)  # Register the hidden popup before creating its opener.
open_settings = manager.make_open_button(
    window=settings,
    rect=Rect(10, 10, 120, 40),
)
manager.add(open_settings)

fps_text = Text(
    rect=Rect(10, 10, 120, 20),
    text=lambda: f"FPS: {backend.clock.get_fps():.0f}",
    color=(255, 255, 255),
)

manager.add(fps_text)

running = True
while running:
    for event in backend.get_events():
        manager.handle_event(event)
        if event.type == EventType.QUIT:
            running = False
    backend.fill_surface("ui_surface", (70, 70, 70))
    manager.draw_all(backend)
    backend.compose_surfaces()
    manager.draw_popups(backend)
    backend.present()

backend.quit()