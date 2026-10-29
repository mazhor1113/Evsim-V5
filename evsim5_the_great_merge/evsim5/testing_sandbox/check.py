import pygame as pg

print("Pygame:", pg.version.ver)

for constant_name in sorted(dir(pg)):
    if not constant_name.startswith("K_"):
        continue

    keycode = getattr(pg, constant_name)

    if not isinstance(keycode, int):
        continue

    print(f"{constant_name:25} -> {pg.key.name(keycode)!r}")