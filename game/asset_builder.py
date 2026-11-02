"""Pixel-art PNG asset generator for Phase Shift.

Needs neither pygame nor Pillow: PNGs are written by hand (zlib + struct).

Output layout (game/assets/ folder):
    characters/<skin>.png   character sprite sheets: 8 frames of 16x16 in a single row
                            0-1 idle, 2-5 run, 6 jump, 7 fall
    environment/            bg.png, tile_top.png, tile_fill.png, coin.png, pad.png, goal.png
    ui/                     button.png, button_active.png, panel.png, input.png (12x12 frames for 9-slice)

Existing files are NOT overwritten, so any PNG can be replaced with your own
(keeping the same frame sizes). The game calls ensure_assets() itself on startup.

Manual run:
    python3 game/asset_builder.py            # create missing files
    python3 game/asset_builder.py --force    # regenerate everything
"""

import random
import struct
import sys
import zlib
from math import sin
from pathlib import Path

CLEAR = (0, 0, 0, 0)
OUTLINE = (18, 22, 36, 255)
WHITE = (255, 255, 255, 255)


def rgba(rgb, alpha=255):
    return (rgb[0], rgb[1], rgb[2], alpha)


class Image:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.px = [[CLEAR for _ in range(width)] for _ in range(height)]

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = color

    def fill_rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def paste_art(self, art, palette, ox=0, oy=0):
        """Draws an image from strings; '.' is a transparent pixel."""
        for dy, row in enumerate(art):
            for dx, ch in enumerate(row):
                if ch != ".":
                    self.set(ox + dx, oy + dy, palette[ch])

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                color = other.px[y][x]
                if color[3]:
                    self.set(ox + x, oy + y, color)

    def save(self, path):
        raw = bytearray()
        for row in self.px:
            raw.append(0)  # row filter: None
            for r, g, b, a in row:
                raw += bytes((r, g, b, a))

        def chunk(tag, data):
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b"")
        )
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)


# --------------------------------------------------------------------------- characters

SKIN_DEFS = {
    "sun": {
        "primary": (247, 180, 70),
        "secondary": (255, 218, 108),
        "accent": (120, 80, 28),
        "crest": [(6, 0, "s"), (7, 0, "s"), (8, 0, "s"), (9, 0, "s")],
    },
    "violet": {
        "primary": (164, 119, 243),
        "secondary": (206, 178, 255),
        "accent": (72, 48, 110),
        "crest": [(4, 0, "s"), (11, 0, "s")],
    },
    "mint": {
        "primary": (92, 224, 158),
        "secondary": (169, 255, 208),
        "accent": (52, 109, 81),
        "crest": [(8, 0, "w")],
    },
}

# Head and body (11 rows), placed starting at row 1.
BODY = [
    "....oooooooo....",
    "...opppppppppo..",
    "..oppppppppppo..",
    "..opppaappaapo..",
    "..opppaappaapo..",
    "..opppppppppo...",
    "...oppppppppo...",
    "..opssssssssp...",
    "..opssssssssp...",
    "...oppppppppo...",
    "....oooooooo....",
]

LEGS_IDLE = [
    ".....aa....aa...",
    ".....aa....aa...",
    ".....aa....aa...",
    "....aaa...aaa...",
]
LEGS_RUN_A = [
    "...aa.......aa..",
    "..aa.........aa.",
    "..aaa.......aaa.",
    "................",
]
LEGS_RUN_B = [
    "......aaaa......",
    "......aaaa......",
    "......aaaa......",
    "......aaaa......",
]
LEGS_RUN_C = [
    "..aa.......aa...",
    ".aa.........aa..",
    ".aaa.......aaa..",
    "................",
]
LEGS_JUMP = [
    "....aa....aa....",
    "....aaa..aaa....",
    "................",
    "................",
]
LEGS_FALL = [
    "....aa......aa..",
    "...aa........aa.",
    "...a..........a.",
    "................",
]

# (legs, body offset downward) for frames 0..7
FRAMES = [
    (LEGS_IDLE, 0),   # 0 idle
    (LEGS_IDLE, 1),   # 1 idle
    (LEGS_RUN_A, 1),  # 2 run
    (LEGS_RUN_B, 0),  # 3 run
    (LEGS_RUN_C, 1),  # 4 run
    (LEGS_RUN_B, 0),  # 5 run
    (LEGS_JUMP, 0),   # 6 jump
    (LEGS_FALL, 0),   # 7 fall
]


def _pad_row(row, width=16):
    """Fits an art row to the given width: trims extra on the right, pads shortfall with dots."""
    return row[:width].ljust(width, ".")


def make_frame(skin, legs, dy):
    palette = {
        "o": OUTLINE,
        "p": rgba(skin["primary"]),
        "s": rgba(skin["secondary"]),
        "a": rgba(skin["accent"]),
        "w": WHITE,
    }
    img = Image(16, 16)
    img.paste_art([_pad_row(r) for r in legs], palette, 0, 12)
    img.paste_art([_pad_row(r) for r in BODY], palette, 0, 1 + dy)
    for x, y, key in skin["crest"]:
        img.set(x, y + dy, palette[key])
    return img


def make_sheet(skin):
    sheet = Image(16 * len(FRAMES), 16)
    for index, (legs, dy) in enumerate(FRAMES):
        sheet.paste(make_frame(skin, legs, dy), index * 16, 0)
    return sheet


# --------------------------------------------------------------------------- environment

def make_tile(top):
    rnd = random.Random(7 if top else 11)
    base, dark, speck = (74, 104, 154), (58, 82, 128), (64, 92, 140)
    mid, light = (96, 135, 196), (150, 190, 235)
    img = Image(16, 16)
    for y in range(16):
        for x in range(16):
            img.set(x, y, rgba(speck if rnd.random() < 0.12 else base))
    for x in range(16):
        img.set(x, 7, rgba(dark))
        img.set(x, 15, rgba(dark))
    start = 3 if top else 0
    for y in range(start, 7):
        img.set(7, y, rgba(dark))
    for y in range(8, 15):
        img.set(3, y, rgba(dark))
        img.set(11, y, rgba(dark))
    if top:
        for x in range(16):
            img.set(x, 0, rgba(light))
            img.set(x, 1, rgba(mid))
            img.set(x, 2, rgba((84, 118, 176)))
    return img


def make_coin():
    sheet = Image(32, 8)
    gold, light, edge = rgba((255, 220, 74)), rgba((255, 245, 180)), rgba((176, 118, 20))
    for frame, half in enumerate((3.5, 2.5, 1.0, 2.5)):
        inside = set()
        for y in range(8):
            for x in range(8):
                nx = (x - 3.5) / half
                ny = (y - 3.5) / 3.9
                if nx * nx + ny * ny <= 1:
                    inside.add((x, y))
        for x, y in inside:
            border = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if border:
                color = edge
            elif half > 2 and (x, y) in ((2, 2), (2, 3)):
                color = light
            else:
                color = gold
            sheet.set(frame * 8 + x, y, color)
    return sheet


PAD_ART = [
    "..oooooooooooooooo..",
    ".orrrrrrrrrrrrrrrro.",
    ".orrrrrrrrrrrrrrrro.",
    "..oooooooooooooooo..",
    "......wwwwwwww......",
    ".......w.ww.w.......",
    "......wwwwwwww......",
    "....gggggggggggg....",
]


def make_pad():
    img = Image(20, 8)
    palette = {
        "o": rgba((120, 30, 45)),
        "r": rgba((242, 104, 119)),
        "w": rgba((220, 225, 235)),
        "g": rgba((140, 150, 170)),
    }
    img.paste_art(PAD_ART, palette)
    return img


def make_goal():
    img = Image(12, 24)
    pole, pole_dark = rgba((210, 216, 232)), rgba((150, 158, 180))
    flag, flag_dark = rgba((92, 221, 146)), rgba((52, 160, 100))
    base, base_light = rgba((120, 130, 150)), rgba((160, 170, 190))
    img.fill_rect(2, 0, 2, 24, pole)
    img.fill_rect(3, 0, 1, 24, pole_dark)
    for y in range(1, 10):
        width = max(1, 8 - 2 * abs(y - 5))
        for x in range(4, 4 + width):
            img.set(x, y, flag)
        img.set(3 + width, y, flag_dark)
    img.fill_rect(0, 21, 6, 3, base)
    img.fill_rect(0, 21, 6, 1, base_light)
    return img


def make_background():
    w, h = 160, 90
    img = Image(w, h)
    top, bottom = (10, 14, 30), (30, 44, 82)
    for y in range(h):
        t = y / (h - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            img.set(x, y, rgba(color))
    rnd = random.Random(42)
    for _ in range(45):
        x, y = rnd.randrange(w), rnd.randrange(55)
        img.set(x, y, rgba((200, 210, 255) if rnd.random() < 0.4 else (120, 135, 180)))
    # moon
    cx, cy, radius = 132, 18, 7
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                img.set(x, y, rgba((226, 232, 252)))
    for x, y in ((130, 15), (135, 21), (133, 13)):
        img.set(x, y, rgba((196, 204, 230)))
    # two layers of mountains
    for x in range(w):
        far = int(60 + 9 * sin(x / 11.0) + 5 * sin(x / 4.3 + 1.0))
        near = int(72 + 7 * sin(x / 7.5 + 2.0) + 4 * sin(x / 3.1))
        for y in range(far, h):
            img.set(x, y, rgba((24, 34, 64)))
        for y in range(near, h):
            img.set(x, y, rgba((16, 24, 46)))
    return img


# --------------------------------------------------------------------------- interface

def make_box(fill, border, highlight=None):
    """A 12x12 frame with rounded corners, for 9-slice (4-pixel border)."""
    img = Image(12, 12)
    corners = {(0, 0), (11, 0), (0, 11), (11, 11)}
    inner_corners = {(1, 1), (10, 1), (1, 10), (10, 10)}
    for y in range(12):
        for x in range(12):
            if (x, y) in corners:
                continue
            edge = x in (0, 11) or y in (0, 11) or (x, y) in inner_corners
            img.set(x, y, rgba(border if edge else fill))
    if highlight:
        for x in range(2, 10):
            img.set(x, 1, rgba(highlight))
    return img


# --------------------------------------------------------------------------- build

def asset_files():
    files = {}
    for skin_id, skin in SKIN_DEFS.items():
        files[f"characters/{skin_id}.png"] = lambda skin=skin: make_sheet(skin)
    files["environment/bg.png"] = make_background
    files["environment/tile_top.png"] = lambda: make_tile(True)
    files["environment/tile_fill.png"] = lambda: make_tile(False)
    files["environment/coin.png"] = make_coin
    files["environment/pad.png"] = make_pad
    files["environment/goal.png"] = make_goal
    files["ui/button.png"] = lambda: make_box((45, 62, 85), (239, 244, 255), (65, 85, 115))
    files["ui/button_active.png"] = lambda: make_box((130, 205, 255), (255, 255, 255), (180, 230, 255))
    files["ui/panel.png"] = lambda: make_box((26, 36, 54), (130, 205, 255))
    files["ui/input.png"] = lambda: make_box((12, 16, 30), (239, 244, 255))
    return files


def build_all(directory, force=False):
    """Creates missing PNGs (or all of them if force). Returns the list of created files."""
    directory = Path(directory)
    created = []
    for name, builder in asset_files().items():
        path = directory / name
        if force or not path.exists():
            builder().save(path)
            created.append(name)
    return created


def ensure_assets(directory):
    return build_all(directory, force=False)


if __name__ == "__main__":
    target = Path(__file__).resolve().with_name("assets")
    done = build_all(target, force="--force" in sys.argv)
    print(f"Assets dir: {target}")
    print("Created:" if done else "Nothing to create, all files exist.")
    for item in done:
        print(" ", item)
