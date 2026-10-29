# Графический backend и пиксельное полотно

## `GraphicsBackend`

`GraphicsBackend` определён в `graphics/protocols.py`. Это `Protocol`: он документирует операции, которыми пользуются виджеты и симуляция. `PygameBackend` — текущая реализация. При переходе на pyglet можно создать другой backend с тем же контрактом, оставив UI-код в основном без изменений.

| Метод | Что делает | Результат |
|---|---|---|
| `compose_surfaces()` | Собирает UI- и simulation-поверхности на главной поверхности | `None` |
| `present()` | Показывает готовый кадр и ограничивает FPS | `int`, прошедшее время кадра в мс |
| `get_fps()` | Возвращает измеренный FPS | `int` |
| `load_image(key, path)` | Загружает изображение из `sprites/` под ключом | `None`; повторный ключ вызывает `ValueError` |
| `get_rect(key, x, y)` | Создаёт прямоугольник с размером текстуры | `Rect` |
| `has_texture(key)` | Проверяет, загружена ли текстура с таким ключом | `bool` |
| `get_texture_size(key)` | Возвращает размер текстуры | `tuple[int, int]` — ширина и высота |
| `draw_canvas(pixels, surface_key)` | Копирует пиксельный массив в поверхность симуляции и композитит его | `None` |
| `draw_texture(surface, key, rect)` | Рисует текстуру с масштабированием до размера `rect` | `None` |
| `draw_text(surface, text, font, color, rect)` | Рисует текст в позиции прямоугольника или пары координат | `None` |
| `fill_surface(surface, color)` | Заполняет поверхность цветом RGB | `None` |
| `get_clip(surface)` | Возвращает текущую область отсечения | `Rect` |
| `set_clip(surface, rect)` | Устанавливает область отсечения; `None` сбрасывает ограничение | `None` |
| `get_events()` | Забирает события pygame и преобразует их в `UIEvent` | `list[UIEvent]` |
| `quit()` | Завершает pygame | `None` |

### Поверхности

- `main_surface` — главное окно pygame.
- `simulation_surface` — поверхность для пикселей симуляции.
- `ui_surface` — отдельная поверхность обычного интерфейса.

`UIManager.draw_all()` рисует обычные UI-элементы на `ui_surface`. Независимые корневые элементырисуются `draw_screen_elements()` непосредственно на `main_surface`, после композиции остальных поверхностей.

### Текстуры

Текстуры адресуются строковыми ключами. Файлы загружаются относительно `sprites/`, поэтому в `load_image()` передавай путь относительно этой папки, например `placeholders/button.png`, а не абсолютный путь машины.

`load_textures(backend)` из `graphics/assets.py` загружает placeholder-набор. Виджеты могут использовать placeholder-ключи, если ключ заданной текстуры отсутствует. Для собственной текстуры сначала загрузи файл, затем используй её ключ в виджете.

## `Canvas`

`Canvas` из `graphics/canvas.py` хранит RGB-массив `pixels` и булеву маску `mask`. Размер задаётся как `(width, height)`; индексация массива идёт как `pixels[x, y]`.

- `Canvas(width, height, background)` — создаёт массив и задаёт фон.
- `Canvas.set_background(color)` — заполняет цветом только пиксели, для которых `mask[x, y]` истинна.
- `draw_pixel(pixels, mask, x, y, color)` — записывает один RGB-пиксель и помечает его как обновлённый (`mask[x, y] = False`).
- `fill_canvas(width, height, pixels, mask, color)` — numba-цикл для заполнения маскированных пикселей.

Функции `fill_canvas` и `draw_pixel` предназначены для горячих циклов работы с массивом; они не рисуют в pygame напрямую. Передавай массивы нужной формы и dtype. Для RGB-массива используется `uint8`, для маски — `bool`.
