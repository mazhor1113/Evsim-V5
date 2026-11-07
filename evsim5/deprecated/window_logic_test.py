"""Headless smoke tests for UI containers; does not require pygame."""
from graphics.event import EventType, UIEvent
from graphics.ui.manager import UIManager
from graphics.ui.widgets import Button, Panel, PopupWindow, Rect, Text


class FakeBackend:
    def __init__(self):
        self.clip = Rect(0, 0, 300, 700)
        self.draw_calls = []

    def get_clip(self, _surface):
        return self.clip

    def set_clip(self, _surface, rect):
        self.clip = rect if rect is not None else Rect(0, 0, 300, 700)

    def draw_texture(self, _surface, texture, rect):
        self.draw_calls.append(("texture", texture, rect))

    def draw_text(self, _surface, text, _font, _color, rect):
        self.draw_calls.append(("text", text, rect))


def run() -> None:
    popup = PopupWindow(Rect(20, 20, 220, 180), visible=False, modal=True, title="Test")
    for index in range(10):
        popup.add(Text(Rect(5, index * 30, 80, 20), f"Row {index}"))

    manager = UIManager(origin=(0, 0))
    manager.add(popup)  # Hidden windows remain in the tree so an opener can show them.
    opener = manager.make_open_button(popup, Rect(5, 5, 40, 30), "unused-in-headless-test")
    owner_window = Panel(Rect(0, 0, 100, 60), children=[opener])
    manager.add(owner_window)

    manager.handle_event(UIEvent(EventType.MOUSE_DOWN, x=10, y=10, button=1))
    manager.handle_event(UIEvent(EventType.MOUSE_UP, x=10, y=10, button=1))
    assert popup.visible and manager.modal_active is popup
    assert popup._scrollbar is not None and popup._scrollbar.visible

    previous_scroll = popup.scroll_y
    manager.handle_event(UIEvent(EventType.MOUSE_WHEEL, x=60, y=80, wheel_y=-2))
    assert popup.scroll_y > previous_scroll
    assert manager._element_at(10, 10) is None  # Modal blocks the opener underneath.

    popup.scroll_y = 0
    popup._sync_chrome()
    close_button = popup._chrome_children[0]
    close_x = popup.rect.x + close_button.rect.x + 3
    close_y = popup.rect.y + close_button.rect.y + 3
    manager.handle_event(UIEvent(EventType.MOUSE_DOWN, x=close_x, y=close_y, button=1))
    manager.handle_event(UIEvent(EventType.MOUSE_UP, x=close_x, y=close_y, button=1))
    assert not popup.visible and manager.modal_active is None

    popup.open()
    start = popup.rect
    resize_x = popup.rect.x + popup.rect.width - 3
    resize_y = popup.rect.y + popup.rect.height - 3
    manager.handle_event(UIEvent(EventType.MOUSE_DOWN, x=resize_x, y=resize_y, button=1))
    manager.handle_event(UIEvent(EventType.MOUSE_MOVE, x=resize_x + 20, y=resize_y + 10))
    manager.handle_event(UIEvent(EventType.MOUSE_UP, x=resize_x + 20, y=resize_y + 10, button=1))
    assert popup.rect.width == start.width + 20
    assert popup.rect.height == start.height + 10

    # A nested panel uses local coordinates and is traversed through the same manager.
    panel = Panel(Rect(5, 5, 100, 60), children=[Text(Rect(2, 2, 30, 12), "Nested")])
    popup.add(panel)
    backend = FakeBackend()
    manager.draw_all(backend)
    assert backend.draw_calls
    assert backend.clip == Rect(0, 0, 300, 700)  # Clip state is restored after drawing.

    # Independent popup coordinates are screen coordinates, not UI-local coordinates.
    offset_manager = UIManager(origin=(900, 0))
    screen_popup = PopupWindow(Rect(350, 80, 220, 160), title="Screen-space", modal=False)
    offset_manager.add(screen_popup)
    ui_clicked = []
    ui_button = Button(Rect(5, 5, 30, 25), "unused", on_click=lambda _arg: ui_clicked.append(True))
    offset_manager.add(ui_button)

    # Popup is interactive outside ui_surface and receives unshifted screen coords.
    assert offset_manager.handle_event(UIEvent(EventType.MOUSE_DOWN, x=360, y=90, button=1)) is True
    assert offset_manager.captured_element is screen_popup
    offset_manager.handle_event(UIEvent(EventType.MOUSE_UP, x=360, y=90, button=1))

    # Ordinary UI is still located in screen space at origin + local rect.
    assert offset_manager.handle_event(UIEvent(EventType.MOUSE_DOWN, x=910, y=10, button=1)) is True
    offset_manager.handle_event(UIEvent(EventType.MOUSE_UP, x=910, y=10, button=1))
    assert ui_clicked == [True]

    # A click outside both popup and UI can be passed to the simulation/debug layer.
    assert offset_manager.handle_event(UIEvent(EventType.MOUSE_DOWN, x=600, y=500, button=1)) is False


if __name__ == "__main__":
    run()
    print("Nested UI smoke tests passed.")
