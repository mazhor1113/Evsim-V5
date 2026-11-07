# Руководство по UI

## 1. Создание элементов

Виджеты находятся в `graphics.ui.widgets`. Их прямоугольник задаётся как `Rect(x, y, width, height)`. Координаты прямоугольника локальны для контейнера, в котором находится элемент.

```python
from graphics.ui.manager import UIManager
from graphics.ui.widgets import Button, Rect, Text, Slider, Panel, PopupWindow

manager = UIManager()

status_text = Text(
    rect=Rect(10, 10, 180, 24),
    text="Simulation ready",
)
manager.add(status_text)

start_button = Button(
    rect=Rect(10, 45, 120, 32),
    texture_key="placeholder_button",
    on_click=lambda _argument: print("Start clicked"),
)
manager.add(start_button)
```

Все корневые элементы обычного интерфейса добавляются в `UIManager` через `add()`. `draw_all(backend)` рисует их на `ui_surface`. В основном цикле программы события нужно передавать в `handle_event()`, а затем вызывать отрисовку и композицию поверхностей.

## 2. Виджеты

### `Rect`

Геометрический прямоугольник с полями `x`, `y`, `width`, `height`.

- `contains(x, y) -> bool` — проверяет, попадает ли точка внутрь прямоугольника. Правая и нижняя границы не включаются.

### `Text`

Показывает текст. Поле `text` может быть строкой или функцией без аргументов. Если это функция, она вызывается при каждой отрисовке — удобно для FPS или счётчиков симуляции.

Основные поля: `rect`, `text`, `font_key`, `color`, `visible`, `enabled`.

### `Button`

Обычная нажимаемая кнопка. `on_click` — необязательный callback, который получает `on_click_argument`. Он вызывается, только если пользователь нажал левую кнопку мыши внутри виджета и отпустил её внутри него.

Основные поля: `rect`, `texture_key`, `pressed_texture_key`, `on_click`, `on_click_argument`, `visible`, `enabled`.

`rect` можно задать явно. Если размер должен совпадать с исходным размером текстуры, разрешается не передавать `rect`, а вместо этого указать `backend`, `x` и `y`:

```python
start_button = Button(
    texture_key="placeholder_button",
    backend=backend,
    x=10,
    y=45,
    on_click=lambda _argument: print("Start clicked"),
)
```

В этом случае конструктор вызывает `backend.get_rect(texture_key, x, y)`: позиция берётся из `x` и `y`, а ширина и высота — из загруженной текстуры. Текстура должна быть загружена до создания виджета. Если `rect` передан явно, `backend`, `x` и `y` для определения размера не нужны.

### `ToggleButton` и `Checkbox`

Переключатели с состоянием `checked`. После завершённого клика состояние инвертируется, а `on_change`, если задан, вызывается с аргументами `(checked, on_change_argument)`.

Как и для `Button`, можно либо передать `rect`, либо передать `backend`, `x` и `y`, чтобы автоматически получить размер по текстуре. Для `ToggleButton` используется текстура, соответствующая начальному значению `checked`; для `Checkbox` — `placeholder_checkbox_off` или `placeholder_checkbox_on`.

`ToggleButton` использует текстуры `placeholder_toggle_button_off` и `placeholder_toggle_button_on` как fallback. `Checkbox` использует соответствующие `placeholder_checkbox_off` и `placeholder_checkbox_on`.

### `Slider`

Ползунок с числовым значением.

- `rect` — область дорожки. Если `rect` не задан, нужно передать `backend`, `x` и `y`: прямоугольник дорожки будет создан по исходному размеру `body_texture_key`.
- `body_texture_key`, `thumb_texture_key` — текстуры дорожки и бегунка.
- `min_value`, `max_value` — диапазон; `max_value` должен быть больше `min_value`.
- `value` — текущее значение, которое ограничивается заданным диапазоном.
- `orientation` — `"horizontal"` или `"vertical"`.
- `thumb_size` — размеры бегунка в пикселях. Если не заданы, в конструктор нужно передать `backend`, чтобы получить размеры `thumb_texture_key`. Для автоматического определения и области дорожки, и бегунка передай `backend`, `x` и `y`, не задавая `rect` и `thumb_size`.
- `on_change` — callback, вызываемый при изменении значения с аргументами `(value, on_change_argument)`.

Пример:

```python
slider = Slider(
    rect=Rect(10, 90, 180, 12),
    body_texture_key="placeholder_slider_body",
    thumb_texture_key="placeholder_slider_thumb",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    thumb_size=(12, 12),
    on_change=lambda value, _argument: print(value),
)
manager.add(slider)
```

Можно также поручить backend определить размер дорожки по `body_texture_key` и размер бегунка по `thumb_texture_key`:

```python
slider = Slider(
    body_texture_key="placeholder_slider_body",
    thumb_texture_key="placeholder_slider_thumb",
    backend=backend,
    x=10,
    y=90,
    value=0.5,
)
```

При таком варианте `body_texture_key` и `thumb_texture_key` должны быть загружены до создания ползунка. `rect` и `thumb_size` можно не указывать: оба размера будут получены из текстур. Если нужна дорожка другого размера, укажи `rect` явно; если нужен бегунок другого размера, укажи `thumb_size`.

### `Panel`

Контейнер для дочерних элементов. В `children` хранятся объекты UI. По умолчанию дочерние элементы обрезаются границами панели (`clip_children=True`).

- `add(element) -> None` — добавить прямого потомка; повторное добавление того же объекта в этот контейнер вызывает `ValueError`.
- `remove(element) -> None` — удалить прямого потомка; если его нет, список выбросит `ValueError`.
- `content_height() -> int` — нижняя граница самого нижнего дочернего элемента в координатах содержимого.
- `child_contexts(parent_offset, parent_clip) -> list[ChildContext]` — возвращает для каждого дочернего элемента тройку `(element, child_offset, child_clip)`. Менеджер использует её для отрисовки, обрезки и проверки попаданий мыши.
- `scrollable=True` включает вертикальную прокрутку колесом мыши. `scroll_y` — текущий сдвиг содержимого.

Пример вложенного контейнера:

```python
panel = Panel(
    rect=Rect(20, 20, 220, 160),
    background_texture_key="placeholder_panel_bg",
    children=[
        Text(Rect(8, 8, 160, 24), "Inside the panel"),
        Button(Rect(8, 40, 100, 30), "placeholder_button"),
    ],
)
manager.add(panel)
```

У дочерней кнопки `Rect(8, 40, ...)` — координаты относительно панели, а не всего экрана. Не прибавляй координаты панели вручную: это делает менеджер.

### `PopupWindow`

Окно на базе `Panel`, которое поддерживает перемещение, изменение размера, сворачивание, закрытие и прокрутку содержимого.

- `title` — текст заголовка.
- `modal=True` — окно блокирует взаимодействие с UI за его пределами.
- `visible=False` — окно можно зарегистрировать заранее и открыть позже.
- `open()` показывает окно и разворачивает его.
- `close()` скрывает окно.
- `minimize()` переключает свёрнутое состояние.
- `min_size=(width, height)` задаёт минимальный размер.
- `resizable` и `draggable` управляют изменением размера и перемещением.
- `max_scroll() -> int` возвращает максимальное вертикальное смещение содержимого.

Независимое окно нужно зарегистрировать через `manager.add(window)`. Чтобы открыть его кнопкой, можно использовать `manager.make_open_button(...)`. Эта кнопка относится к обычному UI, а окно после открытия рисуется поверх него на `main_surface`.

```python
settings = PopupWindow(
    rect=Rect(700, 80, 260, 300),
    title="Settings",
    modal=False,
    visible=False,
)
settings.add(Text(Rect(8, 8, 180, 24), "A setting"))
manager.add(settings)

open_settings = manager.make_open_button(
    window=settings,
    rect=Rect(10, 10, 120, 32),
    texture_key="placeholder_button",
)
manager.add(open_settings)
```

## 3. События и `UIManager`

Бэкенд превращает события pygame в объекты `UIEvent`. Менеджер получает их через `handle_event(event) -> bool`.

- `True`: событие обработано интерфейсом или намеренно заблокировано модальным окном.
- `False`: UI не обработал событие; его можно передать симуляции или другим подсистемам.

Типичные события: `MOUSE_DOWN`, `MOUSE_UP`, `MOUSE_MOVE`, `MOUSE_WHEEL`, `KEY_DOWN`, `KEY_UP`, `TEXT_INPUT`, `WINDOW_FOCUS_LOST`, `RESIZE`, `QUIT`.

`UIManager` также поддерживает захват элемента: после нажатия на кнопку/ползунок перемещение и отпускание продолжают отправляться захваченному элементу, даже если курсор вышел за его границы. При потере фокуса элемент получает `WINDOW_FOCUS_LOST`, чтобы сбросить состояние нажатия или перетаскивания.

## 4. Координатные пространства и порядок кадра

В проекте используются три практически важных пространства:

1. **Экранные координаты** — позиция относительно верхнего левого угла всего окна pygame.
2. **Координаты `ui_surface`** — локальная позиция внутри поверхности интерфейса. Экранная позиция UI-поверхности задаётся `UI_WINDOW_POSITION`.
3. **Локальные координаты контейнера** — позиция дочернего элемента относительно панели или окна.

Независимый корневой `PopupWindow` использует экранные координаты. Дочерние элементы окна используют координаты содержимого окна: начало находится под заголовком. Обычные корневые элементы используют координаты `ui_surface`.

Обычный цикл кадра выглядит так:

```python
for event in backend.get_events():
    consumed = manager.handle_event(event)
    if event.type == EventType.QUIT:
        running = False
    elif not consumed:
        # При необходимости передать событие симуляции/debug-инструментам.
        pass

backend.fill_surface("ui_surface", (70, 70, 70))
manager.draw_all(backend)
backend.compose_surfaces()
manager.draw_screen_elements(backend)
backend.present()
```

`compose_surfaces()` собирает обычные поверхности на `main_surface`, после чего `draw_screen_elements()` рисует независимые элементы поверх композиции. Поэтому не меняй порядок этих вызовов без понимания последствий.

## 5. Внутренние методы

Имена с начальным подчёркиванием — детали реализации, не основной интерфейс для симулятора.

- `_offset_rect(rect, offset)` — создать прямоугольник со смещёнными координатами.
- `_intersection(a, b)` — найти пересечение двух областей отсечения; `None` означает отсутствие ограничения со стороны этого аргумента.
- `Slider._thumb_rect()` — рассчитать положение бегунка.
- `PopupWindow._sync_chrome()` — обновить позиции кнопок заголовка и состояние полосы прокрутки.
- `UIManager._hit_test()` — рекурсивно искать верхний элемент под курсором.
- `UIManager._top_modal_context()` — найти активное модальное окно и его контекст координат/обрезки.
- `UIManager._prune_interaction_state()` — сбросить захват/фокус, если элемент скрыт, выключен или заблокирован модальным окном.

Не вызывай эти методы из кода симуляции, если можно добиться нужного поведения через публичные методы и поля.
