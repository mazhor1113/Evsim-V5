"""Reusable UI elements and geometry helpers.

Coordinates passed to a widget are local to its parent. ``offset`` is added
only while drawing; ``UIManager`` applies the matching inverse transform to
pointer events before forwarding them to the widget.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Literal, TypeAlias

from graphics.event import EventType, UIEvent

if TYPE_CHECKING:
    from graphics.canvas import Canvas
    from graphics.protocols import GraphicsBackend, UIElement, CoordinateSpace

Color: TypeAlias = tuple[int, int, int]
Offset: TypeAlias = tuple[int, int]
ToggleCallback: TypeAlias = Callable[[bool, object], None]
SliderCallback: TypeAlias = Callable[[float, object], None]
@dataclass(frozen=True, slots=True)
class Rect:
    """Integer rectangle used throughout the graphics layer."""

    x: int
    y: int
    width: int
    height: int

    def contains(self, px: int, py: int) -> bool:
        """Return whether point ``(px, py)`` lies inside this rectangle."""
        return (
            self.x <= px < self.x + self.width
            and self.y <= py < self.y + self.height
        )


ChildContext: TypeAlias = tuple["UIElement", Offset, Rect | None]


def _texture_exists(backend: GraphicsBackend, texture_key: str) -> bool:
    """Ask the backend whether a texture exists without exposing its storage."""
    has_texture = getattr(backend, "has_texture", None)
    if has_texture is None:
        # Lightweight fake backends used in tests may accept arbitrary keys.
        return True
    return has_texture(texture_key)


def _infer_rect(
    backend: GraphicsBackend | None,
    texture_key: str,
    x: int | None,
    y: int | None,
) -> Rect:
    """Build a rectangle from a texture's native size and an explicit position."""
    if backend is None:
        raise ValueError(
            "Cannot infer rect without a backend; pass rect=Rect(...) "
            "or provide backend, x, and y."
        )

    if x is None or y is None:
        raise ValueError(
            "Cannot infer rect without a position; provide both x and y."
        )

    if not _texture_exists(backend, texture_key):
        raise ValueError(
            f"Cannot infer rect: texture {texture_key!r} is not loaded."
        )

    return backend.get_rect(texture_key, x, y)


def _offset_rect(rect: Rect, offset: Offset) -> Rect:
    """Return ``rect`` translated by an ``(x, y)`` offset."""
    return Rect(
        x=rect.x + offset[0],
        y=rect.y + offset[1],
        width=rect.width,
        height=rect.height,
    )


def _intersection(a: Rect | None, b: Rect | None) -> Rect | None:
    """Intersect two clipping rectangles; ``None`` means no clipping limit.

    If the rectangles do not overlap, return a zero-sized rectangle at the
    closest intersection corner. This lets callers reliably reject all points.
    """
    if a is None:
        return b
    if b is None:
        return a

    left = max(a.x, b.x)
    top = max(a.y, b.y)
    right = min(a.x + a.width, b.x + b.width)
    bottom = min(a.y + a.height, b.y + b.height)

    if right <= left or bottom <= top:
        return Rect(left, top, 0, 0)

    return Rect(left, top, right - left, bottom - top)


@dataclass(slots=True)
class Text:
    """Draw text; ``text`` may be a string or a zero-argument value provider."""

    rect: Rect
    text: str | Callable[[], object]
    font_key: str = "font_mid"
    color: Color = (0, 0, 0)
    visible: bool = True
    enabled: bool = True
    coordinate_space: CoordinateSpace = "ui"

    def draw(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Render the current text value onto the requested surface."""
        if not self.visible:
            return

        if callable(self.text):
            current_text = self.text()
        else:
            current_text = self.text
        backend.draw_text(
            surface_key,
            str(current_text),
            self.font_key,
            self.color,
            _offset_rect(self.rect, offset),
        )

    def handle_event(self, event: UIEvent) -> None:
        """Text is decorative and does not consume input events."""
        return


@dataclass(slots=True)
class Button:
    """Clickable texture button.

    ``on_click`` receives ``on_click_argument`` after a left-click press and
    release both occur inside the button. Supply ``rect`` explicitly, or pass
    ``backend``, ``x`` and ``y`` to size the rectangle from the texture.
    """

    rect: Rect | None = None
    texture_key: str = "placeholder_button"
    on_click: Callable[[object], None] | None = None
    on_click_argument: object = None
    pressed_texture_key: str = "placeholder_button_pressed"
    visible: bool = True
    enabled: bool = True
    backend: GraphicsBackend | None = field(default=None, repr=False, compare=False)
    x: int | None = None
    y: int | None = None
    _pressed: bool = field(default=False, init=False, repr=False)
    coordinate_space: CoordinateSpace = "ui"

    def __post_init__(self) -> None:
        """Infer the button rectangle from its texture when none was supplied."""
        if self.rect is None:
            self.rect = _infer_rect(
                self.backend,
                self.texture_key,
                self.x,
                self.y,
            )

    def draw(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Draw the normal or pressed texture."""
        if not self.visible:
            return

        assert self.rect is not None
        texture_key = self.texture_key
        if self._pressed and self.pressed_texture_key:
            texture_key = self.pressed_texture_key

        if not _texture_exists(backend, texture_key):
            if self._pressed:
                texture_key = "placeholder_button_pressed"
            else:
                texture_key = "placeholder_button"

        backend.draw_texture(
            surface_key,
            texture_key,
            _offset_rect(self.rect, offset),
        )

    def handle_event(self, event: UIEvent) -> None:
        """Track pointer press/release and invoke the callback on a valid click."""
        if event.type == EventType.WINDOW_FOCUS_LOST:
            self._pressed = False
            return

        if not self.enabled or not self.visible:
            return

        assert self.rect is not None

        if event.type == EventType.MOUSE_DOWN and event.button == 1:
            self._pressed = (
                event.x is not None
                and event.y is not None
                and self.rect.contains(event.x, event.y)
            )
            return

        if event.type != EventType.MOUSE_UP or not self._pressed:
            return

        self._pressed = False
        released_inside = (
            event.x is not None
            and event.y is not None
            and self.rect.contains(event.x, event.y)
        )
        if released_inside and self.on_click is not None:
            if self.on_click_argument is None:
                self.on_click()
            else:
                self.on_click(self.on_click_argument)


@dataclass(slots=True)
class ToggleButton:
    """Button that toggles ``checked`` after a complete left click.

    Supply ``rect`` explicitly, or pass ``backend``, ``x`` and ``y`` to infer
    its size from the texture corresponding to its initial checked state.
    """

    rect: Rect | None = None
    texture_off_key: str = "placeholder_toggle_button_off"
    texture_on_key: str = "placeholder_toggle_button_on"
    checked: bool = False
    on_change: ToggleCallback | None = None
    on_change_argument: object = None
    visible: bool = True
    enabled: bool = True
    backend: GraphicsBackend | None = field(default=None, repr=False, compare=False)
    x: int | None = None
    y: int | None = None
    _pressed: bool = field(default=False, init=False, repr=False)
    coordinate_space: CoordinateSpace = "ui"

    def __post_init__(self) -> None:
        """Infer the toggle rectangle from its initial texture when needed."""
        if self.rect is None:
            texture_key = (
                self.texture_on_key
                if self.checked
                else self.texture_off_key
            )
            self.rect = _infer_rect(
                self.backend,
                texture_key,
                self.x,
                self.y,
            )

    def draw(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Draw the texture corresponding to the current checked state."""
        if not self.visible:
            return

        assert self.rect is not None

        if self.checked:
            texture_key = self.texture_on_key
        else:
            texture_key = self.texture_off_key
        if not _texture_exists(backend, texture_key):
            if self.checked:
                texture_key = "placeholder_toggle_button_on"
            else:
                texture_key = "placeholder_toggle_button_off"

        backend.draw_texture(
            surface_key,
            texture_key,
            _offset_rect(self.rect, offset),
        )

    def handle_event(self, event: UIEvent) -> None:
        """Toggle state on a completed click and notify ``on_change``."""
        if event.type == EventType.WINDOW_FOCUS_LOST:
            self._pressed = False
            return

        if not self.enabled or not self.visible:
            return

        assert self.rect is not None

        if event.type == EventType.MOUSE_DOWN and event.button == 1:
            self._pressed = (
                event.x is not None
                and event.y is not None
                and self.rect.contains(event.x, event.y)
            )
            return

        if event.type != EventType.MOUSE_UP or not self._pressed:
            return

        self._pressed = False
        released_inside = (
            event.x is not None
            and event.y is not None
            and self.rect.contains(event.x, event.y)
        )
        if not released_inside:
            return

        self.checked = not self.checked
        if self.on_change is not None:
            if self.on_change_argument is None:
                self.on_change(self.checked)
            else:
                self.on_change(self.checked, self.on_change_argument)


@dataclass(slots=True)
class Checkbox(ToggleButton):
    """Toggle button using checkbox textures by default."""

    texture_off_key: str = "placeholder_checkbox_off"
    texture_on_key: str = "placeholder_checkbox_on"

    def draw(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Draw the checkbox's checked or unchecked texture."""
        if not self.visible:
            return

        assert self.rect is not None

        if self.checked:
            texture_key = self.texture_on_key
        else:
            texture_key = self.texture_off_key
        if not _texture_exists(backend, texture_key):
            if self.checked:
                texture_key = "placeholder_checkbox_on"
            else:
                texture_key = "placeholder_checkbox_off"

        backend.draw_texture(
            surface_key,
            texture_key,
            _offset_rect(self.rect, offset),
        )


@dataclass(slots=True)
class Slider:
    """Horizontal or vertical numeric slider.

    ``rect`` defines the full track. If ``rect`` is omitted, ``backend``, ``x``
    and ``y`` are required to infer it from the body texture. If ``thumb_size``
    is omitted, ``backend`` is used to read the thumb texture dimensions.
    """

    rect: Rect | None = None
    body_texture_key: str = "placeholder_slider_body"
    thumb_texture_key: str = "placeholder_slider_thumb"
    value: float = 0.0
    min_value: float = 0.0
    max_value: float = 1.0
    thumb_size: tuple[int, int] | None = None
    on_change: SliderCallback | None = None
    on_change_argument: object = None
    visible: bool = True
    enabled: bool = True
    orientation: Literal["horizontal", "vertical"] = "horizontal"
    backend: GraphicsBackend | None = field(default=None, repr=False, compare=False)
    x: int | None = None
    y: int | None = None
    _dragging: bool = field(default=False, init=False, repr=False)
    coordinate_space: CoordinateSpace = "ui"

    def __post_init__(self) -> None:
        """Infer the track rectangle and thumb size, then validate the range."""
        if self.rect is None:
            self.rect = _infer_rect(
                self.backend,
                self.body_texture_key,
                self.x,
                self.y,
            )

        assert self.rect is not None

        if self.max_value <= self.min_value:
            raise ValueError("max_value must be greater than min_value")

        if self.thumb_size is None:
            if self.backend is None:
                raise ValueError(
                    "Provide thumb_size or pass backend to infer it from the thumb texture"
                )
            self.thumb_size = self.backend.get_texture_size(self.thumb_texture_key)

        if self.thumb_size[0] <= 0 or self.thumb_size[1] <= 0:
            raise ValueError("thumb_size dimensions must be positive")

        track_length = self.rect.width
        thumb_length = self.thumb_size[0]
        if self.orientation == "vertical":
            track_length = self.rect.height
            thumb_length = self.thumb_size[1]

        if track_length < thumb_length:
            raise ValueError("Slider track is smaller than its thumb")

        self.value = self._clamp(self.value)

    def _clamp(self, value: float) -> float:
        """Clamp ``value`` to the slider's configured numeric range."""
        if value < self.min_value:
            return self.min_value
        if value > self.max_value:
            return self.max_value
        return value

    def _thumb_rect(self) -> Rect:
        """Calculate the thumb rectangle for the current slider value."""
        assert self.rect is not None
        assert self.thumb_size is not None
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        thumb_width, thumb_height = self.thumb_size

        if self.orientation == "horizontal":
            travel = self.rect.width - thumb_width
            x = round(self.rect.x + ratio * travel)
            y = self.rect.y + (self.rect.height - thumb_height) // 2
            return Rect(x, y, thumb_width, thumb_height)

        travel = self.rect.height - thumb_height
        x = self.rect.x + (self.rect.width - thumb_width) // 2
        y = round(self.rect.y + ratio * travel)
        return Rect(x, y, thumb_width, thumb_height)

    def _set_from_mouse(self, event: UIEvent) -> None:
        """Update the value from the current pointer position."""
        assert self.rect is not None
        assert self.thumb_size is not None

        if self.orientation == "horizontal":
            if event.x is None:
                return
            thumb_length = self.thumb_size[0]
            travel = self.rect.width - thumb_length
            pointer_position = event.x - thumb_length / 2 - self.rect.x
        else:
            if event.y is None:
                return
            thumb_length = self.thumb_size[1]
            travel = self.rect.height - thumb_length
            pointer_position = event.y - thumb_length / 2 - self.rect.y

        if travel <= 0:
            ratio = 0.0
        else:
            ratio = pointer_position / travel

        ratio = max(0.0, min(1.0, ratio))
        new_value = self._clamp(
            self.min_value + ratio * (self.max_value - self.min_value)
        )
        if new_value == self.value:
            return

        self.value = new_value
        if self.on_change is not None:
            if self.on_change_argument is None:
                self.on_change(self.value)
            else:
                self.on_change(self.value, self.on_change_argument)

    def draw(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Draw the track followed by the current thumb position."""
        if not self.visible:
            return

        assert self.rect is not None

        body_key = self.body_texture_key
        if not _texture_exists(backend, body_key):
            body_key = "placeholder_slider_body"

        thumb_key = self.thumb_texture_key
        if not _texture_exists(backend, thumb_key):
            thumb_key = "placeholder_slider_thumb"

        backend.draw_texture(surface_key, body_key, _offset_rect(self.rect, offset))
        backend.draw_texture(
            surface_key,
            thumb_key,
            _offset_rect(self._thumb_rect(), offset),
        )

    def handle_event(self, event: UIEvent) -> None:
        """Capture pointer dragging and update the slider until release."""
        if event.type == EventType.WINDOW_FOCUS_LOST:
            self._dragging = False
            return

        if not self.enabled or not self.visible:
            return

        assert self.rect is not None

        if event.type == EventType.MOUSE_DOWN and event.button == 1:
            pointer_inside = (
                event.x is not None
                and event.y is not None
                and self.rect.contains(event.x, event.y)
            )
            if pointer_inside:
                self._dragging = True
                self._set_from_mouse(event)
            return

        if event.type == EventType.MOUSE_MOVE and self._dragging:
            self._set_from_mouse(event)
            return

        if event.type == EventType.MOUSE_UP and self._dragging:
            self._set_from_mouse(event)
            self._dragging = False


@dataclass(slots=True)
class ResizeHandleBinding:
    """A manually registered Button that resizes its owning Panel."""

    button: Button
    directions: tuple[Literal["left", "right", "top", "bottom"], ...]
    anchor: Literal[
        "left", "right", "top", "bottom",
        "top-left", "top-right", "bottom-left", "bottom-right",
    ]
    stretch: bool = False


@dataclass(slots=True)
class Panel:
    """Container with visibility, child layout, scrolling, and optional resizing.

    Child rectangles use panel-local coordinates. Resizing is opt-in: register
    a custom ``Button`` with ``add_resize_handle``. The panel captures its drag,
    allowing resizing to continue after the pointer leaves the button.
    """

    rect: Rect
    children: list[UIElement] = field(default_factory=list)
    background_texture_key: str | None = "placeholder_panel_bg"
    visible: bool = True
    enabled: bool = True
    clip_children: bool = True
    scrollable: bool = False
    scroll_y: int = 0
    min_size: tuple[int, int] = (1, 1)
    resize_handles: list[ResizeHandleBinding] = field(default_factory=list)
    coordinate_space: CoordinateSpace = "ui"
    _active_resize_handle: ResizeHandleBinding | None = field(
        default=None, init=False, repr=False
    )
    _drag_mode: Literal["move", "resize"] | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _drag_start_mouse: Offset = field(
        default=(0, 0),
        init=False,
        repr=False,
    )
    _drag_start_rect: Rect | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Validate the panel's minimum size; resize handles are opt-in."""
        if self.min_size[0] <= 0 or self.min_size[1] <= 0:
            raise ValueError("min_size dimensions must be positive")
        if self.rect.width < self.min_size[0] or self.rect.height < self.min_size[1]:
            raise ValueError(f"Panel rect must be at least min_size={self.min_size}")

    def open(self) -> None:
        """Make the panel visible."""
        self.visible = True

    def close(self) -> None:
        """Hide the panel and cancel any active resize operation."""
        self.visible = False
        self._cancel_resize()

    def resize_to(self, width: int, height: int) -> None:
        """Set the panel size while enforcing its configured minimum dimensions."""
        self.rect = Rect(
            self.rect.x,
            self.rect.y,
            max(self.min_size[0], width),
            max(self.min_size[1], height),
        )

    def bounds_rect(self) -> Rect:
        """Return the rectangle used for panel hit-testing and clipping."""
        return self.rect

    def add_resize_handle(
        self,
        button: Button,
        directions: tuple[Literal["left", "right", "top", "bottom"], ...],
        *,
        anchor: Literal[
            "left", "right", "top", "bottom",
            "top-left", "top-right", "bottom-left", "bottom-right",
        ] | None = None,
        stretch: bool = False,
    ) -> ResizeHandleBinding:
        """Register a custom Button as a resize grip.

        The button's width and height come from ``button.rect``. ``anchor``
        determines its position relative to the panel; ``stretch=True`` makes
        a top/bottom handle span the panel width, or a left/right handle span
        its height. The button is drawn as an overlay and is not added to
        ``children`` automatically.
        """
        if button.rect is None:
            raise ValueError("Resize handle Button must have an explicit rect")
        allowed = {"left", "right", "top", "bottom"}
        if not directions or set(directions) - allowed:
            raise ValueError("directions must contain left/right/top/bottom")
        if "left" in directions and "right" in directions:
            raise ValueError("Choose either 'left' or 'right' for horizontal resizing")
        if "top" in directions and "bottom" in directions:
            raise ValueError("Choose either 'top' or 'bottom' for vertical resizing")
        if anchor is None:
            horizontal = "left" if "left" in directions else "right" if "right" in directions else None
            vertical = "top" if "top" in directions else "bottom" if "bottom" in directions else None
            if horizontal and vertical:
                anchor = f"{vertical}-{horizontal}"  # type: ignore[assignment]
            else:
                anchor = horizontal or vertical or "bottom-right"
        valid_anchors = {"left", "right", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"}
        if anchor not in valid_anchors:
            raise ValueError(f"Invalid resize handle anchor: {anchor!r}")
        binding = ResizeHandleBinding(button, directions, anchor, stretch)
        self.resize_handles.append(binding)
        self._sync_resize_handles()
        return binding

    def remove_resize_handle(self, button: Button) -> None:
        """Unregister a previously added resize handle Button."""
        self.resize_handles[:] = [item for item in self.resize_handles if item.button is not button]
        if self._active_resize_handle is not None and self._active_resize_handle.button is button:
            self._cancel_resize()

    def _handle_rect(self, binding: ResizeHandleBinding) -> Rect:
        """Calculate a registered handle's panel-local rectangle."""
        assert binding.button.rect is not None
        original = binding.button.rect
        width, height = original.width, original.height
        anchor = binding.anchor
        if binding.stretch and anchor in ("top", "bottom"):
            width = self.rect.width
        elif binding.stretch and anchor in ("left", "right"):
            height = self.rect.height
        if anchor in ("left", "top-left", "bottom-left"):
            x = 0
        elif anchor in ("right", "top-right", "bottom-right"):
            x = self.rect.width - width
        else:
            x = original.x if not binding.stretch else (self.rect.width - width) // 2
        if anchor in ("top", "top-left", "top-right"):
            y = 0
        elif anchor in ("bottom", "bottom-left", "bottom-right"):
            y = self.rect.height - height
        else:
            y = original.y if not binding.stretch else (self.rect.height - height) // 2
        return Rect(x, y, width, height)

    def resize_handle_at(
        self, x: int, y: int, parent_offset: Offset = (0, 0)
    ) -> ResizeHandleBinding | None:
        """Return the topmost enabled resize handle at a parent-space point."""
        panel_x = self.rect.x + parent_offset[0]
        panel_y = self.rect.y + parent_offset[1]
        for binding in reversed(self.resize_handles):
            button = binding.button
            if not button.visible or not button.enabled:
                continue
            rect = self._handle_rect(binding)
            global_rect = Rect(panel_x + rect.x, panel_y + rect.y, rect.width, rect.height)
            if global_rect.contains(x, y):
                return binding
        return None

    def _sync_resize_handles(self, backend: GraphicsBackend | None = None) -> None:
        """Refresh each registered handle's anchored position and optional texture size."""
        for binding in self.resize_handles:
            button = binding.button
            assert button.rect is not None
            if backend is not None and _texture_exists(backend, button.texture_key):
                # Keep the explicitly configured dimensions; the texture is only visual.
                pass
            button.rect = self._handle_rect(binding)

    def draw(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Draw the optional panel background; children are drawn by the manager."""
        if not self.visible or self.background_texture_key is None:
            return

        if _texture_exists(backend, self.background_texture_key):
            backend.draw_texture(
                surface_key,
                self.background_texture_key,
                _offset_rect(self.rect, offset),
            )

    def draw_overlay(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "ui_surface",
    ) -> None:
        """Draw explicitly registered resize buttons above the panel's children."""
        if not self.visible:
            return
        self._sync_resize_handles(backend)
        panel_offset = (self.rect.x + offset[0], self.rect.y + offset[1])
        for binding in self.resize_handles:
            binding.button.draw(backend, panel_offset, surface_key)

    def child_contexts(
        self,
        parent_offset: Offset,
        parent_clip: Rect | None,
    ) -> list[ChildContext]:
        """Return each child with its global offset and inherited clip rectangle."""
        global_rect = _offset_rect(self.rect, parent_offset)
        scroll_offset = self.scroll_y if self.scrollable else 0
        child_offset = (global_rect.x, global_rect.y - scroll_offset)

        if self.clip_children:
            child_clip = _intersection(parent_clip, global_rect)
        else:
            child_clip = parent_clip

        contexts: list[ChildContext] = []
        for child in self.children:
            contexts.append((child, child_offset, child_clip))
        return contexts

    def content_height(self) -> int:
        """Return the bottom-most child edge in panel-local coordinates."""
        bottom_edges: list[int] = []
        for child in self.children:
            bottom_edges.append(child.rect.y + child.rect.height)
        if not bottom_edges:
            return 0
        return max(bottom_edges)

    def _cancel_resize(self) -> None:
        """Reset resize capture and release the active handle's visual state."""
        self._drag_mode = None
        self._drag_start_rect = None
        if self._active_resize_handle is not None:
            self._active_resize_handle.button._pressed = False
        self._active_resize_handle = None

    def _resize_from_drag(self, event: UIEvent) -> None:
        """Apply pointer movement to the edges selected by the active handle."""
        if self._drag_start_rect is None or self._active_resize_handle is None:
            return
        if event.x is None or event.y is None:
            return
        start_rect = self._drag_start_rect
        delta_x = event.x - self._drag_start_mouse[0]
        delta_y = event.y - self._drag_start_mouse[1]
        directions = set(self._active_resize_handle.directions)
        x, y, width, height = start_rect.x, start_rect.y, start_rect.width, start_rect.height
        if "left" in directions:
            width = max(self.min_size[0], start_rect.width - delta_x)
            x = start_rect.x + start_rect.width - width
        elif "right" in directions:
            width = max(self.min_size[0], start_rect.width + delta_x)
        if "top" in directions:
            height = max(self.min_size[1], start_rect.height - delta_y)
            y = start_rect.y + start_rect.height - height
        elif "bottom" in directions:
            height = max(self.min_size[1], start_rect.height + delta_y)
        self.rect = Rect(x, y, width, height)
        self._sync_resize_handles()

    def handle_event(self, event: UIEvent) -> None:
        """Handle custom resize-handle dragging and mouse-wheel scrolling."""
        if event.type == EventType.WINDOW_FOCUS_LOST:
            self._cancel_resize()
            return
        if not self.visible or not self.enabled:
            return
        if event.type == EventType.MOUSE_DOWN and event.button == 1:
            if event.x is None or event.y is None:
                return
            panel_local_x = event.x - self.rect.x
            panel_local_y = event.y - self.rect.y
            binding = next((
                item for item in reversed(self.resize_handles)
                if item.button.visible and item.button.enabled
                and self._handle_rect(item).contains(panel_local_x, panel_local_y)
            ), None)
            if binding is not None:
                self._active_resize_handle = binding
                self._drag_mode = "resize"
                self._drag_start_mouse = (event.x, event.y)
                self._drag_start_rect = self.rect
                binding.button._pressed = True
            return
        if event.type == EventType.MOUSE_MOVE and self._drag_mode == "resize":
            self._resize_from_drag(event)
            return
        if event.type == EventType.MOUSE_UP and self._drag_mode == "resize":
            self._resize_from_drag(event)
            self._cancel_resize()
            return
        if event.type != EventType.MOUSE_WHEEL or not self.scrollable or not event.wheel_y:
            return
        if event.x is None or event.y is None or not self.rect.contains(event.x, event.y):
            return
        maximum_scroll = max(0, self.content_height() - self.rect.height)
        self.scroll_y -= event.wheel_y * 30
        self.scroll_y = max(0, min(maximum_scroll, self.scroll_y))

    def add(self, element: UIElement) -> None:
        """Append a child, rejecting duplicate direct children."""
        if element in self.children:
            raise ValueError("Element is already a child of this panel")
        self.children.append(element)

    def remove(self, element: UIElement) -> None:
        """Remove a direct child; raise ``ValueError`` if it is not present."""
        self.children.remove(element)


@dataclass(slots=True)
class PopupWindow(Panel):
    """Movable, resizable popup with title-bar controls and automatic scrolling.

    An independent popup registered directly with ``UIManager`` uses screen
    coordinates and is rendered on ``main_surface``. Its child coordinates are
    relative to the content area below the title bar.

    Resizing is opt-in: register one or more custom Button instances with
    ``add_resize_handle``. This also applies to ordinary Panel instances.
    """

    bg_texture_key: str = "placeholder_window_bg"
    title_texture_key: str = "placeholder_window_title"
    title: str = ""
    title_color: Color = (255, 255, 255)
    modal: bool = False
    titlebar_height: int = 28
    min_size: tuple[int, int] = (140, 90)
    draggable: bool = True
    collapsed: bool = False
    scrollbar_width: int = 12

    close_texture_key: str = "placeholder_window_close"
    pressed_texture_key: str = "placeholder_button_pressed"
    minimize_texture_key: str = "placeholder_window_hide"

    scrollbar_body_texture_key: str = "placeholder_slider_body"
    scrollbar_thumb_texture_key: str = "placeholder_slider_thumb"
    chrome_children: list[UIElement] | None = None
    auto_generate_chrome_buttons: bool = True

    resize_texture_key: str = "placeholder_window_resize"
    resize_pressed_texture_key: str = "placeholder_button_pressed"
    auto_generate_resize_handle: bool = True
    coordinate_space: CoordinateSpace = "screen"

    _auto_chrome_buttons: bool = field(default=False, init=False, repr=False)
    _chrome_children: list[UIElement] = field(
        default_factory=list,
        init=False,
        repr=False,
    )
    _scrollbar: Slider | None = field(
        default=None,
        init=False,
        repr=False,
    )
    def __post_init__(self) -> None:
        """Validate window geometry and create default chrome when requested."""
        if (
            self.rect.width < self.min_size[0]
            or self.rect.height < self.min_size[1]
        ):
            raise ValueError(
                f"PopupWindow rect must be at least min_size={self.min_size}"
            )
        if self.titlebar_height <= 0 or self.titlebar_height >= self.rect.height:
            raise ValueError(
                "titlebar_height must be positive and smaller "
                "than the window height"
            )

        # Set up the inherited resize handle and validate shared Panel options.
        Panel.__post_init__(self)
        # Create the default resize handle for PopupWindow.
        if self.auto_generate_resize_handle and not self.resize_handles:
            default_resize_button = Button(
                rect=Rect(0, 0, 20, 20),
                texture_key=self.resize_texture_key,
                pressed_texture_key=self.resize_pressed_texture_key,
            )

            self.add_resize_handle(
                default_resize_button,
                directions=("left", "bottom"),
                anchor="bottom-left",
            )

        custom_chrome = bool(self.chrome_children)
        self._auto_chrome_buttons = (
            self.auto_generate_chrome_buttons and not custom_chrome
        )
        if custom_chrome:
            self._chrome_children = self.chrome_children
        elif self._auto_chrome_buttons:
            close_button = Button(
                rect=Rect(0, 0, 1, 1),
                texture_key=self.close_texture_key,
                on_click=self._close_clicked,
                pressed_texture_key=self.pressed_texture_key,
            )
            minimize_button = Button(
                rect=Rect(0, 0, 1, 1),
                texture_key=self.minimize_texture_key,
                on_click=self._minimize_clicked,
                pressed_texture_key=self.pressed_texture_key,
            )
            self._chrome_children = [close_button, minimize_button]
        else:
            self._chrome_children = []

        self.chrome_children = self._chrome_children
        scrollbar_height = self.rect.height - self.titlebar_height
        self._scrollbar = Slider(
            rect=Rect(
                0,
                self.titlebar_height,
                self.scrollbar_width,
                max(1, scrollbar_height),
            ),
            body_texture_key=self.scrollbar_body_texture_key,
            thumb_texture_key=self.scrollbar_thumb_texture_key,
            value=0.0,
            thumb_size=(self.scrollbar_width, self.scrollbar_width),
            on_change=self._scrollbar_changed,
            orientation="vertical",
            visible=False,
        )
        self._chrome_children.append(self._scrollbar)
        self.chrome_children = self._chrome_children
        self._sync_chrome()

    def bounds_rect(self) -> Rect:
        """Return the visible window bounds, including minimized state."""
        height = self.rect.height

        if self.collapsed:
            height = self.titlebar_height

        return Rect(
            self.rect.x,
            self.rect.y,
            self.rect.width,
            height,
        )

    def open(self) -> None:
        """Show the window and restore its expanded state."""
        self.visible = True
        self.collapsed = False
        self._sync_chrome()

    def close(self) -> None:
        """Hide the window and cancel any active move or resize operation."""
        Panel.close(self)

    def minimize(self) -> None:
        """Toggle between the full window and its title bar."""
        self.collapsed = not self.collapsed
        Panel._cancel_resize(self)
        self._sync_chrome()

    def _close_clicked(self, _argument: object = None) -> None:
        """Handle a click on the close button."""
        self.close()

    def _minimize_clicked(self, _argument: object = None) -> None:
        """Handle a click on the minimize button."""
        self.minimize()

    def _scrollbar_changed(
        self,
        value: float,
        _argument: object = None,
    ) -> None:
        """Convert the normalized scrollbar value to a content offset."""
        self.scroll_y = round(value * self.max_scroll())

    def max_scroll(self) -> int:
        """Return the maximum vertical scroll offset for the current content."""
        viewport_height = max(
            0,
            self.rect.height - self.titlebar_height,
        )
        scroll_range = self.content_height() - viewport_height

        if scroll_range < 0:
            return 0

        return scroll_range

    def _sync_chrome(
        self,
        backend: GraphicsBackend | None = None,
    ) -> None:
        """Position title-bar controls and synchronize the scrollbar.

        If custom chrome elements are appended to ``chrome_children`` after
        construction, remove the generated close/minimize buttons automatically.
        """
        width = self.rect.width
        height = self.rect.height

        if self._auto_chrome_buttons and len(self._chrome_children) >= 2:
            generated_close = self._chrome_children[0]
            generated_minimize = self._chrome_children[1]
            has_custom_chrome = False
            for child in self._chrome_children:
                if (
                    child is not generated_close
                    and child is not generated_minimize
                    and child is not self._scrollbar
                ):
                    has_custom_chrome = True
                    break
            if has_custom_chrome:
                self._chrome_children = [
                    child
                    for child in self._chrome_children
                    if child is not generated_close
                    and child is not generated_minimize
                ]
                self.chrome_children = self._chrome_children
                self._auto_chrome_buttons = False

        if self._auto_chrome_buttons and len(self._chrome_children) >= 2:
            close_button = self._chrome_children[0]
            minimize_button = self._chrome_children[1]
            assert isinstance(close_button, Button)
            assert isinstance(minimize_button, Button)

            if backend is not None:
                if _texture_exists(backend, self.close_texture_key):
                    close_width, close_height = backend.get_texture_size(
                        self.close_texture_key
                    )
                    close_button.rect = Rect(0, 0, close_width, close_height)
                if _texture_exists(backend, self.minimize_texture_key):
                    minimize_width, minimize_height = backend.get_texture_size(
                        self.minimize_texture_key
                    )
                    minimize_button.rect = Rect(0, 0, minimize_width, minimize_height)

            assert close_button.rect is not None
            assert minimize_button.rect is not None
            close_width = close_button.rect.width
            close_height = close_button.rect.height
            minimize_width = minimize_button.rect.width
            minimize_height = minimize_button.rect.height

            close_button.rect = Rect(
                width - close_width - 5,
                (self.titlebar_height - close_height) // 2,
                close_width,
                close_height,
            )
            minimize_button.rect = Rect(
                close_button.rect.x - minimize_width - 3,
                (self.titlebar_height - minimize_height) // 2,
                minimize_width,
                minimize_height,
            )

        assert self._scrollbar is not None
        maximum_scroll = self.max_scroll()
        overflow = maximum_scroll > 0

        scrollbar_height = height - self.titlebar_height
        self._scrollbar.rect = Rect(
            width - self.scrollbar_width,
            self.titlebar_height,
            self.scrollbar_width,
            max(1, scrollbar_height),
        )

        self.scroll_y = max(0, min(maximum_scroll, self.scroll_y))
        self._scrollbar.visible = overflow and not self.collapsed
        self._scrollbar.enabled = overflow and not self.collapsed
        if maximum_scroll == 0:
            self._scrollbar.value = 0.0
        else:
            self._scrollbar.value = self.scroll_y / maximum_scroll

        self._sync_resize_handles(backend)

    def draw(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "main_surface",
    ) -> None:
        """Draw the window, title bar, controls, and resize handle."""
        if not self.visible:
            return

        self._sync_chrome(backend)

        rect = self.bounds_rect()
        screen_rect = _offset_rect(rect, offset)

        # Draw the main window background.
        backend.draw_texture(
            surface_key,
            self.bg_texture_key,
            screen_rect,
        )

        # Draw the title-bar texture separately from the window background.
        titlebar_rect = Rect(
            screen_rect.x,
            screen_rect.y,
            screen_rect.width,
            self.titlebar_height,
        )
        backend.draw_texture(
            surface_key,
            self.title_texture_key,
            titlebar_rect,
        )

        # Keep the optional textual title on top of the title-bar texture.
        if self.title:
            title_text_rect = Rect(
                screen_rect.x + 7,
                screen_rect.y + 5,
                max(0, screen_rect.width - 55),
                max(1, self.titlebar_height - 5),
            )
            backend.draw_text(
                surface_key,
                self.title,
                "font_small",
                self.title_color,
                title_text_rect,
            )

        # The resize handle is a Button drawn by draw_overlay() after children.
        self._sync_resize_handles(backend)

    def draw_overlay(
        self,
        backend: GraphicsBackend,
        offset: Offset = (0, 0),
        surface_key: str = "main_surface",
    ) -> None:
        """Draw the resize button after the window's content and chrome."""
        if self.collapsed:
            return
        Panel.draw_overlay(self, backend, offset, surface_key)

    def child_contexts(
        self,
        parent_offset: Offset,
        parent_clip: Rect | None,
    ) -> list[ChildContext]:
        """Return child offsets and clipping rectangles for UIManager."""
        self._sync_chrome()

        global_rect = _offset_rect(self.rect, parent_offset)

        if self.collapsed:
            title_rect = Rect(
                global_rect.x,
                global_rect.y,
                global_rect.width,
                self.titlebar_height,
            )
            chrome_clip = _intersection(parent_clip, title_rect)

            contexts: list[ChildContext] = []
            for child in self._chrome_children:
                if child is self._scrollbar:
                    continue
                contexts.append(
                    (child, (global_rect.x, global_rect.y), chrome_clip)
                )
            return contexts

        maximum_scroll = self.max_scroll()

        reserved_scrollbar_width = 0
        if maximum_scroll > 0:
            reserved_scrollbar_width = self.scrollbar_width

        content_width = max(
            0,
            self.rect.width - reserved_scrollbar_width,
        )
        content_height = max(
            0,
            self.rect.height - self.titlebar_height,
        )

        content_rect = Rect(
            global_rect.x,
            global_rect.y + self.titlebar_height,
            content_width,
            content_height,
        )
        content_clip = _intersection(parent_clip, content_rect)

        content_offset = (
            global_rect.x,
            global_rect.y + self.titlebar_height - self.scroll_y,
        )
        chrome_clip = _intersection(parent_clip, global_rect)

        contexts: list[ChildContext] = []

        for child in self.children:
            contexts.append(
                (
                    child,
                    content_offset,
                    content_clip,
                )
            )

        for child in self._chrome_children:
            contexts.append(
                (
                    child,
                    (global_rect.x, global_rect.y),
                    chrome_clip,
                )
            )

        return contexts

    def handle_event(self, event: UIEvent) -> None:
        """Handle title-bar movement, inherited resizing, and window scrolling."""
        if event.type == EventType.WINDOW_FOCUS_LOST:
            Panel.handle_event(self, event)
            self._drag_start_rect = None
            return

        if not self.visible or not self.enabled:
            return

        if event.type == EventType.MOUSE_DOWN and event.button == 1:
            if event.x is None or event.y is None:
                return

            if not self.collapsed and self.resize_handle_at(event.x, event.y) is not None:
                Panel.handle_event(self, event)
                return

            in_title_bar = (
                self.draggable
                and self.rect.x <= event.x < self.rect.x + self.rect.width
                and self.rect.y <= event.y < self.rect.y + self.titlebar_height
            )
            if in_title_bar:
                self._drag_mode = "move"
                self._drag_start_mouse = (event.x, event.y)
                self._drag_start_rect = self.rect
            else:
                self._drag_mode = None
                self._drag_start_rect = None
            return

        if event.type == EventType.MOUSE_MOVE:
            if self._drag_mode == "move" and self._drag_start_rect is not None:
                if event.x is None or event.y is None:
                    return
                delta_x = event.x - self._drag_start_mouse[0]
                delta_y = event.y - self._drag_start_mouse[1]
                start_rect = self._drag_start_rect
                self.rect = Rect(
                    start_rect.x + delta_x,
                    start_rect.y + delta_y,
                    start_rect.width,
                    start_rect.height,
                )
                self._sync_chrome()
                return
            Panel.handle_event(self, event)
            return

        if event.type == EventType.MOUSE_UP:
            if self._drag_mode == "move":
                self._drag_mode = None
                self._drag_start_rect = None
                return
            Panel.handle_event(self, event)
            return

        if (
            event.type == EventType.MOUSE_WHEEL
            and event.wheel_y
            and not self.collapsed
        ):
            if event.x is None or event.y is None:
                return
            if not self.rect.contains(event.x, event.y):
                return

            maximum_scroll = self.max_scroll()
            self.scroll_y -= event.wheel_y * 30
            self.scroll_y = max(0, min(maximum_scroll, self.scroll_y))
            if self._scrollbar is not None and maximum_scroll > 0:
                self._scrollbar.value = self.scroll_y / maximum_scroll
            return

        Panel.handle_event(self, event)

    def add(self, element: UIElement) -> None:
        """Add a content child and update the scrollbar."""
        if (
            element in self.children
            or element in self._chrome_children
        ):
            raise ValueError("Element is already a child of this window")

        self.children.append(element)
        self._sync_chrome()

    def remove(self, element: UIElement) -> None:
        """Remove a content child and update the scrollbar."""
        self.children.remove(element)
        self._sync_chrome()

@dataclass(slots=True)
class SimulationViewport:
    canvas: Canvas

    rect: Rect | None = None

    visible: bool = True
    enabled: bool = True
    _pressed: bool = False
    _pixel_selection_active: bool = False
    _area_selection_active: bool = False

    _first_position: tuple[int, int] | None = None
    _mouse_pointing_to: tuple[int, int] | None = None

    selected_pixel_position: tuple[int, int] | None = None
    selected_rect: Rect | None = None

    selection_sprite_key: str = "selection"

    coordinate_space: CoordinateSpace = "screen"

    def __post_init__(self) -> None:
        """Rect is created automatically"""
        if self.rect is None:
            self.rect = self.canvas.rect

    def activate_pixel_selection(self) -> None:
        self._pixel_selection_active = True

    def activate_area_selection(self) -> None:
        self._area_selection_active = True

    def draw(
        self,
        backend: GraphicsBackend,
        offset: tuple[int, int] = (0, 0),
        surface_key: str = "main_surface",
    ) -> None:
        if self.visible and self.enabled:
            backend.draw_pixels(
                self.rect.x + offset[0],
                self.rect.y + offset[1],
                self.canvas.pixels,
                self.canvas.scale,
            )

            if self._pixel_selection_active and self._mouse_pointing_to is not None:
                pixel = Rect(
                    self._mouse_pointing_to[0],
                    self._mouse_pointing_to[1],
                    self.canvas.scale,
                    self.canvas.scale,
                )
                backend.draw_texture(
                    surface_key,
                    self.selection_sprite_key,
                    pixel,
                )
            positions_exist = self._first_position is not None and self._mouse_pointing_to is not None
            if self._area_selection_active and positions_exist:
                first_x = max(self._first_position[0], self._mouse_pointing_to[0])
                first_y = max(self._first_position[1], self._mouse_pointing_to[1])
                last_x = min(self._first_position[0], self._mouse_pointing_to[0])
                last_y = min(self._first_position[1], self._mouse_pointing_to[1])

                selection_width = first_x - last_x
                selection_height = first_y - last_y

                selection_rect = Rect(
                    last_x,
                    last_y,
                    selection_width,
                    selection_height,
                )
                backend.draw_texture(
                    surface_key,
                    self.selection_sprite_key,
                    selection_rect,
                )

    def handle_event(self, event: UIEvent) -> None:
        if event.type == EventType.WINDOW_FOCUS_LOST:
            self._pressed = False
            return

        if not self.enabled or not self.visible:
            return

        assert self.rect is not None, "SimulationViewport rect is None"

        if event.type == EventType.MOUSE_DOWN and event.button == 1:
            self._pressed = (
                event.x is not None
                and event.y is not None
                and self.rect.contains(event.x, event.y)
            )
            if self._pressed and self._area_selection_active:
                self._first_position = event.x, event.y
            return

        if event.type == EventType.MOUSE_MOVE:
            self._mouse_pointing_to = event.x, event.y

        if event.type == EventType.MOUSE_UP and self._pressed:
            self._pressed = False
            released_inside = self.rect.contains(event.x, event.y)

            if released_inside:
                print("detected")
                if self._pixel_selection_active:
                    self.selected_pixel_position = event.x, event.y
                    self._pixel_selection_active = False
    
                if self._area_selection_active:
                    first_x = max(self._first_position[0], event.x)
                    first_y = max(self._first_position[1], event.y)
                    last_x = min(self._first_position[0], event.x)
                    last_y = min(self._first_position[1], event.y)
    
                    selection_width = first_x - last_x
                    selection_height = first_y - last_y
    
                    self.selected_rect = Rect(
                        last_x,
                        last_y,
                        selection_width,
                        selection_height,
                    )
                    self._area_selection_active = False
                    self._first_position = None