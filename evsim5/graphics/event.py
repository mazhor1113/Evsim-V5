"""Backend-independent input event types used by the UI manager and widgets."""

from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """Normalized event categories, independent of pygame's event constants."""

    MOUSE_DOWN = auto()
    MOUSE_UP = auto()
    MOUSE_MOVE = auto()
    MOUSE_WHEEL = auto()

    KEY_DOWN = auto()
    KEY_UP = auto()
    TEXT_INPUT = auto()

    QUIT = auto()
    WINDOW_FOCUS_LOST = auto()
    WINDOW_RESIZE = auto()


@dataclass(frozen=True, slots=True)
class UIEvent:
    """Immutable input event with optional pointer, keyboard and window data.

    Coordinates are screen-space coordinates when first emitted by a backend.
    ``UIManager`` creates translated copies when forwarding events to children.
    """

    type: EventType
    x: int | None = None
    y: int | None = None
    button: int | None = None
    key: str | None = None
    modifiers: frozenset[str] = frozenset()
    text: str | None = None
    wheel_x: int = 0
    wheel_y: int = 0
    width: int | None = None
    height: int | None = None
