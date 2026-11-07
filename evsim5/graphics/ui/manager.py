from __future__ import annotations

from dataclasses import replace
from typing import Literal, TypeAlias

import config.config as config
from graphics.event import EventType, UIEvent
from graphics.protocols import GraphicsBackend, UIElement
from graphics.ui.widgets import (
    Button,
    Panel,
    PopupWindow,
    Rect,
    _intersection,
    _offset_rect,
    CoordinateSpace,
)

HitResult: TypeAlias = tuple[UIElement, tuple[int, int], CoordinateSpace]
ModalContext: TypeAlias = tuple[PopupWindow, tuple[int, int], Rect | None, CoordinateSpace]
ScrollContext: TypeAlias = tuple[Panel, tuple[int, int], CoordinateSpace]


class UIManager:
    """Owns UI trees and routes screen-space events to the correct coordinate space.

    Contract:
    - Ordinary root UI elements use coordinates local to ``ui_surface``.
    - Independent root PopupWindow instances use screen coordinates and are drawn
      directly onto ``main_surface``.
    - Events received by handle_event() always retain the backend's screen coords.
    - The return value is True when the UI consumes/blocks an event, False when
      it can be passed to another system (e.g. the simulation/debug tools).
    """

    def __init__(self, origin: tuple[int, int] | None = None) -> None:
        self.elements: list[UIElement] = []
        self.captured_element: UIElement | None = None
        self.focused_element: UIElement | None = None

        self.origin = origin if origin is not None else config.UI_WINDOW_POSITION

        self._captured_parent_offset = (0, 0)
        self._captured_space = "ui"

        self._base_clip = Rect(
            0,
            0,
            config.UI_WINDOW_SIZE[0],
            config.UI_WINDOW_SIZE[1],
        )

        self._screen_clip = Rect(
            0,
            0,
            config.SCREENSIZE[0],
            config.SCREENSIZE[1],
        )

        # Сохраняем отступы интерфейса от краёв окна.
        self._ui_right_margin = (
            config.SCREENSIZE[0]
            - config.UI_WINDOW_POSITION[0]
            - config.UI_WINDOW_SIZE[0]
        )

        self._ui_top_margin = config.UI_WINDOW_POSITION[1]

    @property
    def modal_active(self) -> PopupWindow | None:
        """Return the top active modal popup, if one currently exists."""
        context = self._top_modal_context()
        if context is None:
            return None
        return context[0]

    def add(self, element: UIElement) -> None:
        """Register a root UI element, rejecting duplicates and already-owned items."""
        if element in self.elements:
            raise ValueError("Element is already a root UI element")
        if self._is_in_tree(element):
            raise ValueError("Element already belongs to another UI container")
        self.elements.append(element)

    def open_window(self, window: PopupWindow) -> None:
        """Open and raise an independent root popup; its rect is in screen coords."""
        if window not in self.elements:
            raise ValueError(
                "An independent popup must be registered with UIManager.add(window) first"
            )
        window.open()
        self.elements.remove(window)
        self.elements.append(window)

    def remove(self, element: UIElement) -> None:
        """Remove a root element and clear interaction state that points to it."""
        if element in self.elements:
            self.elements.remove(element)
        if self.captured_element is element:
            self.captured_element = None
            self._captured_parent_offset = (0, 0)
        if self.focused_element is element:
            self.focused_element = None

    def draw_all(self, backend: GraphicsBackend) -> None:
        """Draw ordinary UI roots to ui_surface, using UI-local coordinates."""
        previous_clip = backend.get_clip("ui_surface")
        self._base_clip = previous_clip
        try:
            for element in self._ordered_roots():
                if self._root_space(element) != "ui":
                    continue

                self._draw_tree(
                    backend,
                    element,
                    (0, 0),
                    previous_clip,
                    "ui_surface",
                )
        finally:
            backend.set_clip("ui_surface", previous_clip)

    def draw_screen_elements(self, backend: GraphicsBackend) -> None:
        """Draw independent popup roots to ``main_surface`` in screen coordinates."""
        previous_clip = backend.get_clip("main_surface")
        popup_clip = _intersection(previous_clip, self._screen_clip)
        try:
            for element in self._ordered_roots():
                if self._root_space(element) != "screen":
                    continue

                self._draw_tree(
                    backend,
                    element,
                    (0, 0),
                    popup_clip,
                    "main_surface",
                )
        finally:
            backend.set_clip("main_surface", previous_clip)

    def _ordered_roots(self) -> list[UIElement]:
        """Return root elements in drawing order, with modal trees on top."""
        return sorted(
            self.elements,
            key=lambda item: (
                self._tree_has_modal(item),
                self._root_space(item) == "screen",
            ),
        )

    def _tree_has_modal(self, element: UIElement) -> bool:
        """Return whether this element tree contains an active modal popup."""
        if (
            isinstance(element, PopupWindow)
            and element.visible
            and element.enabled
            and element.modal
        ):
            return True
        if isinstance(element, Panel):
            children = list(element.children)
            chrome_children = getattr(element, "_chrome_children", [])
            children.extend(chrome_children)
            for child in children:
                if self._tree_has_modal(child):
                    return True
        return False

    def _draw_tree(
        self,
        backend: GraphicsBackend,
        element: UIElement,
        parent_offset: tuple[int, int],
        parent_clip: Rect | None,
        surface_key: str,
    ) -> None:
        """Draw an element, its descendants, and its foreground overlay."""
        if not element.visible:
            return

        backend.set_clip(surface_key, parent_clip)
        element.draw(backend, parent_offset, surface_key)

        if isinstance(element, Panel):
            child_contexts = element.child_contexts(
                parent_offset,
                parent_clip,
            )

            for child, child_offset, child_clip in child_contexts:
                self._draw_tree(
                    backend,
                    child,
                    child_offset,
                    child_clip,
                    surface_key,
                )

        # Draw resize handles above all child content. Panels and windows use
        # the same overlay hook; PopupWindow only changes its surface and chrome.
        if isinstance(element, Panel):
            backend.set_clip(surface_key, parent_clip)
            element.draw_overlay(backend, parent_offset, surface_key)

    def _root_space(self, element: UIElement) -> CoordinateSpace:
        """Return the coordinate space declared by a root element."""
        return element.coordinate_space

    def _screen_to_ui(self, event: UIEvent) -> UIEvent:
        """Convert screen-space pointer coordinates to UI-surface coordinates."""
        if event.x is None or event.y is None:
            return event
        return replace(
            event,
            x=event.x - self.origin[0],
            y=event.y - self.origin[1],
        )

    def _is_inside_ui_screen_rect(self, x: int, y: int) -> bool:
        """Return whether a screen point falls inside the ordinary UI surface."""
        ui_screen_rect = Rect(
            self.origin[0],
            self.origin[1],
            config.UI_WINDOW_SIZE[0],
            config.UI_WINDOW_SIZE[1],
        )
        return ui_screen_rect.contains(x, y)

    def _element_at_screen(
            self,
            x: int,
            y: int,
        ) -> HitResult | None:
        """Hit-test roots using their declared coordinate spaces."""

        modal_context = self._top_modal_context()

        # A modal restricts interaction to its own tree.
        if modal_context is not None:
            modal, parent_offset, parent_clip, space = modal_context

            if space == "screen":
                return self._hit_test(
                    modal,
                    x,
                    y,
                    parent_offset,
                    parent_clip,
                    "screen",
                )

            if not self._is_inside_ui_screen_rect(x, y):
                return None

            local_event = self._screen_to_ui(
                UIEvent(EventType.MOUSE_MOVE, x=x, y=y)
            )

            return self._hit_test(
                modal,
                local_event.x,
                local_event.y,
                parent_offset,
                parent_clip,
                "ui",
            )

        # Screen-space roots are tested first, from top to bottom.
        for root in reversed(self._ordered_roots()):
            if self._root_space(root) != "screen":
                continue

            hit = self._hit_test(
                root,
                x,
                y,
                (0, 0),
                self._screen_clip,
                "screen",
            )

            if hit is not None:
                return hit

        # UI-space roots exist only inside ui_surface.
        if not self._is_inside_ui_screen_rect(x, y):
            return None

        local_event = self._screen_to_ui(
            UIEvent(EventType.MOUSE_MOVE, x=x, y=y)
        )

        for root in reversed(self._ordered_roots()):
            if self._root_space(root) != "ui":
                continue

            hit = self._hit_test(
                root,
                local_event.x,
                local_event.y,
                (0, 0),
                self._base_clip,
                "ui",
            )

            if hit is not None:
                return hit

        return None

    def _element_at(
        self,
        x: int,
        y: int,
    ) -> tuple[UIElement, tuple[int, int]] | None:
        """Compatibility helper returning the hit element and parent offset."""
        hit = self._element_at_screen(x, y)
        if hit is None:
            return None
        return hit[0], hit[1]

    def _hit_test(
        self,
        element: UIElement,
        x: int,
        y: int,
        parent_offset: tuple[int, int],
        parent_clip: Rect | None,
        space: CoordinateSpace,
    ) -> HitResult | None:
        """Recursively find the topmost child that contains a pointer point."""
        if not element.visible or not element.enabled:
            return None

        if isinstance(element, Panel):
            local_bounds = element.bounds_rect()
        else:
            local_bounds = element.rect

        global_rect = _offset_rect(local_bounds, parent_offset)

        if parent_clip is not None and not parent_clip.contains(x, y):
            return None

        if isinstance(element, Panel):
            is_collapsed_window = (
                isinstance(element, PopupWindow) and element.collapsed
            )
            if (
                not is_collapsed_window
                and element.resize_handle_at(x, y, parent_offset)
            ):
                # Route the press to the owning panel; it captures the drag so
                # resizing continues even after the pointer leaves the handle.
                return element, parent_offset, space

        if isinstance(element, Panel):
            child_contexts = element.child_contexts(
                parent_offset,
                parent_clip,
            )
            for child, child_offset, child_clip in reversed(child_contexts):
                hit = self._hit_test(
                    child,
                    x,
                    y,
                    child_offset,
                    child_clip,
                    space,
                )
                if hit is not None:
                    return hit

        visible_rect = _intersection(parent_clip, global_rect)
        if visible_rect is not None and visible_rect.contains(x, y):
            return element, parent_offset, space

        return None

    def _scrollable_at_screen(
        self,
        x: int,
        y: int,
    ) -> ScrollContext | None:
        """Find the deepest scrollable panel under a screen-space point."""
        hit = self._element_at_screen(x, y)
        if hit is None:
            return None

        _target, _offset, space = hit
        event = UIEvent(EventType.MOUSE_MOVE, x=x, y=y)
        if space == "ui":
            event = self._screen_to_ui(event)

        # Prefer the deepest scrollable container in the same coordinate space.
        found: ScrollContext | None = None
        modal_context = self._top_modal_context()

        if modal_context:
            roots = [
                (
                    modal_context[0],
                    modal_context[1],
                    modal_context[2],
                    modal_context[3],
                )
            ]
        else:
            roots: list[
                tuple[
                    UIElement,
                    tuple[int, int],
                    Rect | None,
                    CoordinateSpace,
                ]
            ] = []

            roots = []

            for root in self._ordered_roots():
                space = self._root_space(root)

                if space == "screen":
                    roots.append(
                        (root, (0, 0), self._screen_clip, "screen")
                    )

                elif space == "ui" and self._is_inside_ui_screen_rect(x, y):
                    roots.append(
                        (root, (0, 0), self._base_clip, "ui")
                    )

        def visit(
            element: UIElement,
            parent_offset: tuple[int, int],
            parent_clip: Rect | None,
            root_space: CoordinateSpace,
        ) -> None:
            """Visit a visible subtree and remember the deepest scrollable panel."""
            nonlocal found

            if (
                not element.visible
                or not element.enabled
                or root_space != space
            ):
                return

            if space == "screen":
                px, py = x, y
            else:
                px, py = event.x, event.y

            if px is None or py is None:
                return

            if parent_clip is not None and not parent_clip.contains(px, py):
                return

            if isinstance(element, Panel):
                own_rect = _offset_rect(
                    element.bounds_rect(),
                    parent_offset,
                )

                if isinstance(element, PopupWindow):
                    maximum_scroll = element.max_scroll()
                    scrollable = (
                        not element.collapsed and maximum_scroll > 0
                    )
                    reserved_scrollbar_width = 0
                    if maximum_scroll > 0:
                        reserved_scrollbar_width = element.scrollbar_width

                    content_width = max(
                        0,
                        own_rect.width - reserved_scrollbar_width,
                    )
                    content_height = max(
                        0,
                        own_rect.height - element.titlebar_height,
                    )
                    content_rect = Rect(
                        own_rect.x,
                        own_rect.y + element.titlebar_height,
                        content_width,
                        content_height,
                    )
                else:
                    scrollable = (
                        element.scrollable
                        and element.content_height() > element.rect.height
                    )
                    content_rect = own_rect

                if scrollable and content_rect.contains(px, py):
                    found = (element, parent_offset, space)

                child_contexts = element.child_contexts(
                    parent_offset,
                    parent_clip,
                )
                for child, child_offset, child_clip in child_contexts:
                    visit(
                        child,
                        child_offset,
                        child_clip,
                        root_space,
                    )

        for root, offset, clip, root_space in roots:
            visit(root, offset, clip, root_space)

        return found

    def _top_modal_context(self) -> ModalContext | None:
        """Return the active modal, its parent offset, clip and coordinate space."""
        found: ModalContext | None = None

        def visit(
            element: UIElement,
            parent_offset: tuple[int, int],
            parent_clip: Rect | None,
            space: CoordinateSpace,
        ) -> None:
            """Search a subtree for the topmost visible modal window."""
            nonlocal found

            if not element.visible or not element.enabled:
                return

            if isinstance(element, Panel):
                local_bounds = element.bounds_rect()
            else:
                local_bounds = element.rect

            effective_rect = _offset_rect(
                local_bounds,
                parent_offset,
            )
            visible_part = _intersection(parent_clip, effective_rect)

            if visible_part is not None and (
                visible_part.width == 0 or visible_part.height == 0
            ):
                return

            if isinstance(element, PopupWindow) and element.modal:
                found = (
                    element,
                    parent_offset,
                    parent_clip,
                    space,
                )

            if isinstance(element, Panel):
                child_contexts = element.child_contexts(
                    parent_offset,
                    parent_clip,
                )
                for child, child_offset, child_clip in child_contexts:
                    visit(
                        child,
                        child_offset,
                        child_clip,
                        space,
                    )

        for root in self._ordered_roots():
            space = self._root_space(root)

            if space == "screen":
                visit(
                    root,
                    (0, 0),
                    self._screen_clip,
                    "screen",
                )

            else:
                visit(
                    root,
                    (0, 0),
                    self._base_clip,
                    "ui",
                )

        return found

    def _contains(self, root: UIElement, target: UIElement) -> bool:
        """Return whether ``target`` is root or a descendant of ``root``."""
        if root is target:
            return True

        if isinstance(root, Panel):
            children = list(root.children)
            children.extend(getattr(root, "_chrome_children", []))

            for child in children:
                if self._contains(child, target):
                    return True

        return False

    def _is_in_tree(self, target: UIElement) -> bool:
        """Return whether an element already belongs to any registered tree."""
        for root in self.elements:
            if self._contains(root, target):
                return True
        return False

    def _is_effectively_available(self, target: UIElement) -> bool:
        """Check the element and all its ancestors are visible and enabled."""

        def visit(
            element: UIElement,
            ancestors_available: bool,
        ) -> bool:
            """Return whether the target is available along this tree branch."""
            available = (
                ancestors_available
                and element.visible
                and element.enabled
            )

            if element is target:
                return available

            if isinstance(element, Panel):
                children = list(element.children)
                children.extend(getattr(element, "_chrome_children", []))

                for child in children:
                    if visit(child, available):
                        return True

            return False

        for root in self.elements:
            if visit(root, True):
                return True

        return False

    def _prune_interaction_state(self) -> None:
        """Release capture/focus when an element becomes unavailable or blocked."""
        modal = self.modal_active

        if self.captured_element is not None:
            captured_unavailable = not self._is_effectively_available(
                self.captured_element
            )
            blocked_by_modal = (
                modal is not None
                and not self._contains(modal, self.captured_element)
            )

            if captured_unavailable or blocked_by_modal:
                self.captured_element.handle_event(
                    UIEvent(EventType.WINDOW_FOCUS_LOST)
                )
                self.captured_element = None
                self._captured_parent_offset = (0, 0)

        if self.focused_element is not None:
            focused_unavailable = not self._is_effectively_available(
                self.focused_element
            )
            blocked_by_modal = (
                modal is not None
                and not self._contains(modal, self.focused_element)
            )

            if focused_unavailable or blocked_by_modal:
                self.focused_element.handle_event(
                    UIEvent(EventType.WINDOW_FOCUS_LOST)
                )
                self.focused_element = None

    def _handle_window_resize(self, width: int, height: int, backend: GraphicsBackend) -> None:
        """Update global window geometry and reposition the UI surface."""

        if width <= 0 or height <= 0:
            return

        # Обновляем глобальные размеры окна.
        backend.screensize = (width, height)

        # UI surface закреплена за правым верхним углом.
        ui_width, ui_height = backend.ui_window_size

        x = max(
            0,
            width - ui_width - self._ui_right_margin,
        )

        y = max(
            0,
            self._ui_top_margin,
        )

        self.origin = (x, y)

        # Обновляем глобальное положение UI surface.
        config.UI_WINDOW_POSITION = self.origin

        # Обновляем границы доступных областей.
        self._screen_clip = Rect(0, 0, width, height)

        self._base_clip = Rect(
            0,
            0,
            ui_width,
            ui_height,
        )

    def handle_event(self, event: UIEvent) -> bool:
        """Route an event; return True if UI consumes or intentionally blocks it."""
        if event.type == EventType.QUIT:
            return False

        if event.type == EventType.WINDOW_RESIZE:
            if event.width is not None and event.height is not None:
                self._handle_window_resize(event.width, event.height)

            for element in self.elements:
                element.handle_event(event)

            return True

        if event.type == EventType.WINDOW_FOCUS_LOST:
            for target in (self.captured_element, self.focused_element):
                if target is not None:
                    target.handle_event(event)

            self.captured_element = self.focused_element = None
            self._captured_parent_offset = (0, 0)
            return False

        self._prune_interaction_state()
        has_position = event.x is not None and event.y is not None

        if event.type == EventType.MOUSE_DOWN:
            if not has_position:
                return False

            hit = self._element_at_screen(event.x, event.y)

            if hit is None:
                if self.modal_active is not None:
                    # A modal blocks clicks even when they land outside its rectangle.
                    return True

                self.focused_element = None
                return False

            element, parent_offset, space = hit
            target_event = self._event_for_parent(
                event,
                parent_offset,
                space,
            )

            self.captured_element = element
            self._captured_parent_offset = parent_offset
            self._captured_space = space
            self.focused_element = element

            element.handle_event(target_event)
            self._prune_interaction_state()
            return True

        if event.type in (EventType.MOUSE_MOVE, EventType.MOUSE_UP):
            if self.captured_element is not None:
                target_event = self._event_for_parent(
                    event,
                    self._captured_parent_offset,
                    self._captured_space,
                )

                self.captured_element.handle_event(target_event)

                if event.type == EventType.MOUSE_UP:
                    self.captured_element = None
                    self._captured_parent_offset = (0, 0)

                self._prune_interaction_state()
                return True

            if event.type == EventType.MOUSE_MOVE and has_position:
                hit = self._element_at_screen(event.x, event.y)

                if hit:
                    element, parent_offset, space = hit
                    target_event = self._event_for_parent(
                        event,
                        parent_offset,
                        space,
                    )
                    element.handle_event(target_event)
                    return True

            return False

        if event.type == EventType.MOUSE_WHEEL:
            if not has_position:
                return False

            modal_blocks_pointer = (
                self.modal_active is not None
                and self._element_at_screen(event.x, event.y) is None
            )

            if modal_blocks_pointer:
                return True

            scroll_target = self._scrollable_at_screen(
                event.x,
                event.y,
            )

            if scroll_target:
                element, parent_offset, space = scroll_target
                target_event = self._event_for_parent(
                    event,
                    parent_offset,
                    space,
                )
                element.handle_event(target_event)
                return True

            hit = self._element_at_screen(event.x, event.y)

            if hit:
                element, parent_offset, space = hit
                target_event = self._event_for_parent(
                    event,
                    parent_offset,
                    space,
                )
                element.handle_event(target_event)
                return True

            return False

        if event.type in (
                EventType.KEY_DOWN,
                EventType.KEY_UP,
                EventType.TEXT_INPUT,
            ):
            target = self.focused_element
            modal = self.modal_active

            if modal and (
                target is None or not self._contains(modal, target)
            ):
                target = modal

            if target is not None:
                target.handle_event(event)
                return True

            return modal is not None

        return False

    def _event_for_parent(
        self,
        event: UIEvent,
        parent_offset: tuple[int, int],
        space: CoordinateSpace,
    ) -> UIEvent:
        """Convert an event to the coordinate space expected by a child element."""
        if space == "ui":
            event = self._screen_to_ui(event)

        if event.x is None or event.y is None:
            return event

        return replace(
            event,
            x=event.x - parent_offset[0],
            y=event.y - parent_offset[1],
        )