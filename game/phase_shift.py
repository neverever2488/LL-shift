"""Phase Shift — a retro platform game: pixel art, menus, skins and a local leaderboard."""

import json
import sys
from datetime import datetime
from pathlib import Path

import requests

# --------------------------------------------------------------------------- server API
# The game no longer touches any database file: all results go through the API,
# so there is exactly one database (the one in the api folder).
SERVER_URL = "http://127.0.0.1:8000"
SCORES_URL = f"{SERVER_URL}/api/scores"            # POST: save a result
LEADERBOARD_URL = f"{SERVER_URL}/api/leaderboard"  # GET: top results
LEADERBOARD_LIMIT = 10


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from game.asset_builder import ensure_assets
from game.logic import validate_nickname


# --------------------------------------------------------------------------- constants

# The game field is 1280x720. The window is resizable: the image is scaled with black bars.
W, H = 1280, 720
FPS = 60

# Levels are authored in 960x600 coordinates; they are stretched to W x H on load.
BASE_W, BASE_H = 960, 600
LEVEL_SX, LEVEL_SY = W / BASE_W, H / BASE_H

PLAYER_SIZE = 32          # 16 px art * SPRITE_SCALE
SPRITE_SCALE = 2
TILE_SCALE = 2            # 16 px tile -> 32 px
UI_SCALE = 3              # 12 px UI frames -> 36 px (12 px border)
COIN_DRAW = 16            # 8 px coin art * 2
COIN_HITBOX = 22
PLAYER_SPEED = 5
GRAVITY = 0.62
MAX_FALL_SPEED = 14
LEVEL_TIME = 90
MAX_JUMP_CHARGE = 0.65
HUD_HEIGHT = 64
TEMP_W, TEMP_H = 112, 16
TEMP_LIFETIME = 2.8
MAX_TEMP_PLATFORMS = 2

TEXT = (239, 244, 255)
ACCENT = (130, 205, 255)
COIN = (255, 220, 74)
PANEL = (26, 36, 54)
ERROR = (255, 120, 120)
MEDALS = [(255, 220, 74), (205, 212, 225), (214, 150, 96)]

RAW_LEVELS = [
    {
        "name": "Level 1 - First Steps",
        "spawn": (70, 480),
        "platforms": [(0, 550, 260, 50), (325, 485, 160, 20), (550, 415, 160, 20), (775, 345, 150, 20)],
        "coins": [(390, 440), (615, 370), (840, 300)],
        "pads": [],
        "goal": (865, 275, 35, 70),
    },
    {
        "name": "Level 2 - Spring Trail",
        "spawn": (55, 480),
        "platforms": [(0, 550, 190, 50), (255, 490, 100, 20), (425, 425, 110, 20), (620, 350, 105, 20), (800, 270, 120, 20)],
        "coins": [(290, 445), (475, 380), (670, 305), (850, 225)],
        "pads": [(120, 530, 45, 20)],
        "goal": (855, 200, 35, 70),
    },
    {
        "name": "Level 3 - Build Your Path",
        "spawn": (45, 480),
        "platforms": [(0, 550, 180, 50), (290, 460, 100, 20), (500, 365, 95, 20), (735, 260, 170, 20)],
        "coins": [(325, 415), (540, 320), (680, 400), (810, 215)],
        "pads": [(120, 530, 45, 20)],
        "goal": (845, 190, 35, 70),
    },
    {
        "name": "Level 4 - Final Run",
        "spawn": (35, 480),
        "platforms": [(0, 550, 150, 50), (230, 500, 80, 20), (405, 425, 85, 20), (605, 330, 85, 20), (805, 215, 115, 20)],
        "coins": [(265, 455), (445, 380), (645, 285), (755, 365), (855, 170)],
        "pads": [(95, 530, 40, 20), (430, 405, 35, 20)],
        "goal": (855, 145, 35, 70),
    },
]

# Sprite sheet frames: 0-1 idle, 2-5 run, 6 jump, 7 fall (16x16 each, a single row).
ANIMATIONS = {
    "idle": {"frames": [0, 1], "frame_time": 0.45},
    "run": {"frames": [2, 3, 4, 5], "frame_time": 0.09},
    "jump": {"frames": [6], "frame_time": 1.0},
    "fall": {"frames": [7], "frame_time": 1.0},
}

SKINS = [
    {"id": "sun", "name": "Sun Runner", "sheet": "characters/sun.png", "frame_size": (16, 16), "animations": ANIMATIONS},
    {"id": "violet", "name": "Violet Dash", "sheet": "characters/violet.png", "frame_size": (16, 16), "animations": ANIMATIONS},
    {"id": "mint", "name": "Mint Shift", "sheet": "characters/mint.png", "frame_size": (16, 16), "animations": ANIMATIONS},
]


def _sx(value):
    return int(round(value * LEVEL_SX))


def _sy(value):
    return int(round(value * LEVEL_SY))


def _scale_rect(x, y, w, h):
    return pygame.Rect(_sx(x), _sy(y), _sx(w), _sy(h))


def build_levels():
    levels = []
    for item in RAW_LEVELS:
        levels.append(
            {
                "name": item["name"],
                "spawn": (_sx(item["spawn"][0]), _sy(item["spawn"][1])),
                "platforms": [_scale_rect(*p) for p in item["platforms"]],
                "coins": [(_sx(x), _sy(y)) for x, y in item["coins"]],
                "pads": [_scale_rect(*p) for p in item["pads"]],
                "goal": _scale_rect(*item["goal"]),
            }
        )
    return levels


LEVELS = build_levels()


# --------------------------------------------------------------------------- assets

class Assets:
    """Loads PNGs from game/assets/ (missing ones are created by asset_builder) and caches scaled copies."""

    def __init__(self):
        ensure_assets(ASSETS_DIR)
        self._skin_cache = {}
        self._platform_cache = {}
        self._nine_cache = {}
        self._sized_cache = {}

        self.background = pygame.transform.scale(self.load("environment/bg.png"), (W, H)).convert()
        self.tile_top = self.scaled("environment/tile_top.png", TILE_SCALE)
        self.tile_fill = self.scaled("environment/tile_fill.png", TILE_SCALE)

        coin_sheet = self.load("environment/coin.png")
        size = coin_sheet.get_height()
        self.coin_frames = [
            pygame.transform.scale(coin_sheet.subsurface((i * size, 0, size, size)), (COIN_DRAW, COIN_DRAW))
            for i in range(coin_sheet.get_width() // size)
        ]
        self.ui = {name: self.scaled(f"ui/{name}.png", UI_SCALE) for name in ("button", "button_active", "panel", "input")}

    @staticmethod
    def load(name):
        return pygame.image.load(str(ASSETS_DIR / name)).convert_alpha()

    def scaled(self, name, factor):
        image = self.load(name)
        return pygame.transform.scale(image, (image.get_width() * factor, image.get_height() * factor))

    def sized(self, name, size):
        """Image stretched (nearest-neighbor) to the given size: spring pads, finish flag."""
        key = (name, size)
        if key not in self._sized_cache:
            self._sized_cache[key] = pygame.transform.scale(self.load(name), size)
        return self._sized_cache[key]

    def skin_frames(self, skin, scale=SPRITE_SCALE):
        """List of skin frames as [(facing right, facing left), ...] at the requested scale."""
        key = (skin["id"], scale)
        if key not in self._skin_cache:
            sheet = self.load(skin["sheet"])
            fw, fh = skin["frame_size"]
            frames = []
            for i in range(sheet.get_width() // fw):
                frame = sheet.subsurface((i * fw, 0, fw, fh))
                right = pygame.transform.scale(frame, (fw * scale, fh * scale))
                frames.append((right, pygame.transform.flip(right, True, False)))
            self._skin_cache[key] = frames
        return self._skin_cache[key]

    def platform(self, width, height, tinted=False):
        """Platform of the given size built from tiles (the top row uses the edge tile)."""
        key = (width, height, tinted)
        if key not in self._platform_cache:
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            tile_size = self.tile_top.get_width()
            for ty in range(0, height, tile_size):
                tile = self.tile_top if ty == 0 else self.tile_fill
                for tx in range(0, width, tile_size):
                    surface.blit(tile, (tx, ty))
            if tinted:
                surface.fill((70, 10, 90, 0), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.rect(surface, (14, 20, 38), surface.get_rect(), 2)
            self._platform_cache[key] = surface
        return self._platform_cache[key]

    def nine_slice(self, name, size):
        """Stretches a UI frame to the given size without distorting the corners."""
        key = (name, size)
        if key not in self._nine_cache:
            image = self.ui[name]
            iw, ih = image.get_size()
            b = 4 * UI_SCALE
            w, h = size
            result = pygame.Surface(size, pygame.SRCALPHA)
            xs_src, ys_src = [0, b, iw - b, iw], [0, b, ih - b, ih]
            xs_dst, ys_dst = [0, b, w - b, w], [0, b, h - b, h]
            for j in range(3):
                for i in range(3):
                    src = pygame.Rect(xs_src[i], ys_src[j], xs_src[i + 1] - xs_src[i], ys_src[j + 1] - ys_src[j])
                    dw, dh = xs_dst[i + 1] - xs_dst[i], ys_dst[j + 1] - ys_dst[j]
                    if dw <= 0 or dh <= 0:
                        continue
                    patch = image.subsurface(src)
                    if patch.get_size() != (dw, dh):
                        patch = pygame.transform.scale(patch, (dw, dh))
                    result.blit(patch, (xs_dst[i], ys_dst[j]))
            self._nine_cache[key] = result
        return self._nine_cache[key]


# --------------------------------------------------------------------------- player

class Player:
    def __init__(self, pos, skin, assets):
        self.skin = skin
        self.rect = pygame.Rect(*pos, PLAYER_SIZE, PLAYER_SIZE)
        self.velocity = pygame.Vector2()
        self.on_ground = False
        self.jump_charge = 0.0
        self.facing = 1
        self.frames = assets.skin_frames(skin)
        self.anim = "idle"
        self.frame_index = 0
        self.anim_timer = 0.0

    def update(self, keys, platforms, dt):
        direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.velocity.x = direction * PLAYER_SPEED
        if direction:
            self.facing = direction

        self.rect.x += round(self.velocity.x)
        for block in platforms:
            if self.rect.colliderect(block):
                if self.velocity.x > 0:
                    self.rect.right = block.left
                elif self.velocity.x < 0:
                    self.rect.left = block.right
        # keep the player inside the field
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(W, self.rect.right)

        self.velocity.y = min(self.velocity.y + GRAVITY, MAX_FALL_SPEED)
        self.rect.y += round(self.velocity.y)
        self.on_ground = False
        for block in platforms:
            if self.rect.colliderect(block):
                if self.velocity.y >= 0:
                    self.rect.bottom = block.top
                    self.on_ground = True
                else:
                    self.rect.top = block.bottom
                self.velocity.y = 0

        # Jump charge accumulates in real time, not per frame.
        if self.jump_charge:
            if self.on_ground:
                self.jump_charge = min(self.jump_charge + dt, MAX_JUMP_CHARGE)
            else:
                self.jump_charge = 0.0

        self.update_animation(direction, dt)

    def update_animation(self, direction, dt):
        if not self.on_ground:
            name = "jump" if self.velocity.y < 0 else "fall"
        elif direction:
            name = "run"
        else:
            name = "idle"
        if name != self.anim:
            self.anim = name
            self.frame_index = 0
            self.anim_timer = 0.0
        spec = self.skin["animations"][name]
        self.anim_timer += dt
        if self.anim_timer >= spec["frame_time"]:
            self.anim_timer -= spec["frame_time"]
            self.frame_index = (self.frame_index + 1) % len(spec["frames"])

    def release_jump(self):
        if self.jump_charge and self.on_ground:
            power = 9 + min(self.jump_charge, MAX_JUMP_CHARGE) * 9
            self.velocity.y = -power
            self.on_ground = False
        self.jump_charge = 0.0

    def draw(self, surface):
        spec = self.skin["animations"][self.anim]
        index = spec["frames"][self.frame_index % len(spec["frames"])]
        right, left = self.frames[index]
        image = left if self.facing < 0 else right
        if self.jump_charge:  # crouch while charging a jump
            squash = int(8 * min(1.0, self.jump_charge / MAX_JUMP_CHARGE))
            image = pygame.transform.scale(image, (image.get_width(), image.get_height() - squash))
        surface.blit(image, (self.rect.x, self.rect.bottom - image.get_height()))


# --------------------------------------------------------------------------- game

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Phase Shift")
        self.window = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.canvas = pygame.Surface((W, H))
        self.view_scale = 1.0
        self.view_offset = (0, 0)
        self.assets = Assets()
        self.clock = pygame.time.Clock()
        self.anim_time = 0.0
        self.font = pygame.font.Font(None, 34)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 84)
        self.menu_items = ["Start", "Leaderboard", "Choose Skin", "Quit"]
        self.menu_index = 0
        self.selected_skin_id = SKINS[0]["id"]
        self.selected_skin_index = 0
        self.nickname = "Player"
        self.name_buffer = self.nickname
        self.name_entry_active = False
        self.name_error = ""
        self.state = "MENU"
        self.level_index = 0
        self.run_time = 0.0
        self.banked_coins = 0  # coins from completed levels
        self.level_coins = 0   # coins from the current level attempt
        self.completed = False
        self.saved_result = False
        self.message = ""
        self.message_timer = 0.0
        self.settings_path = Path(__file__).resolve().with_name("settings.json")
        self.load_settings()
        self.leaderboard = self.fetch_leaderboard()
        self.load_level()

    # ------------------------------------------------------------------ data

    @property
    def total_coins(self):
        return self.banked_coins + self.level_coins

    def current_skin(self):
        return next((skin for skin in SKINS if skin["id"] == self.selected_skin_id), SKINS[0])

    def load_settings(self):
        payload = {}
        if self.settings_path.exists():
            try:
                payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
        self.selected_skin_id = payload.get("selected_skin", self.selected_skin_id)
        nickname = payload.get("nickname", self.nickname)
        if not isinstance(nickname, str) or not validate_nickname(nickname.strip()):
            nickname = "Player"
        self.nickname = nickname.strip()
        self.selected_skin_index = next(
            (index for index, skin in enumerate(SKINS) if skin["id"] == self.selected_skin_id), 0
        )
        self.selected_skin_id = SKINS[self.selected_skin_index]["id"]
        self.name_buffer = self.nickname

    def save_settings(self):
        payload = {"selected_skin": self.selected_skin_id, "nickname": self.nickname}
        try:
            self.settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass

    def fetch_leaderboard(self):
        """Top results from the API. Returns [] if the server is unavailable."""
        try:
            response = requests.get(LEADERBOARD_URL, timeout=3)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            print("Failed to load leaderboard:", exc)
            return []

        # accept both a plain list and {"items": [...]} / {"scores": [...]}
        if isinstance(data, dict):
            data = data.get("items") or data.get("scores") or data.get("results") or []

        rows = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                rows.append(
                    {
                        "nickname": str(item.get("nickname", "?")),
                        "total_time": float(item.get("total_time", 0)),
                        "coins": int(item.get("coins", 0)),
                        "skin": str(item.get("skin", "")),
                        "played_on": str(item.get("played_on", "")),
                    }
                )
            except (TypeError, ValueError):
                continue
        return rows[:LEADERBOARD_LIMIT]

    # ------------------------------------------------------------------ logic

    def load_level(self):
        data = LEVELS[self.level_index]
        self.player = Player(data["spawn"], self.current_skin(), self.assets)
        self.platforms = [rect.copy() for rect in data["platforms"]]
        self.coins = [pygame.Rect(x - COIN_HITBOX // 2, y - COIN_HITBOX // 2, COIN_HITBOX, COIN_HITBOX) for x, y in data["coins"]]
        self.pads = [rect.copy() for rect in data["pads"]]
        self.goal = data["goal"].copy()
        self.temp_platforms = []
        self.level_elapsed = 0.0
        self.level_coins = 0  # when a level restarts the coins respawn, so the count is reset too

    def reset_run(self):
        self.level_index = 0
        self.banked_coins = 0
        self.level_coins = 0
        self.completed = False
        self.run_time = 0.0
        self.saved_result = False
        self.message = ""
        self.message_timer = 0.0
        self.load_level()

    def start_run(self):
        candidate = self.name_buffer.strip()
        if not validate_nickname(candidate):
            self.name_error = "Use 3-16 letters, numbers, or underscores."
            return
        self.nickname = candidate
        self.save_settings()
        self.reset_run()
        self.state = "PLAYING"
        self.name_entry_active = False
        self.name_error = ""
        self.name_buffer = self.nickname

    def begin_name_entry(self):
        self.name_buffer = self.nickname
        self.name_entry_active = True
        self.name_error = ""

    def create_platform(self):
        if len(self.temp_platforms) >= MAX_TEMP_PLATFORMS:
            return
        x = self.player.rect.centerx + self.player.facing * 64 - TEMP_W // 2
        y = self.player.rect.bottom + 24
        rect = pygame.Rect(max(0, min(W - TEMP_W, x)), min(H - 40, y), TEMP_W, TEMP_H)
        if not any(rect.colliderect(block) for block in self.platforms):
            self.temp_platforms.append([rect, TEMP_LIFETIME])

    def update(self, dt):
        if self.state != "PLAYING":
            return
        self.run_time += dt
        self.level_elapsed += dt
        self.message_timer = max(0, self.message_timer - dt)

        keys = pygame.key.get_pressed()
        blocks = self.platforms + [item[0] for item in self.temp_platforms]
        self.player.update(keys, blocks, dt)

        for pad in self.pads:
            if self.player.rect.colliderect(pad) and self.player.velocity.y >= 0:
                self.player.rect.bottom = pad.top
                self.player.velocity.y = -15

        self.temp_platforms = [[rect, left - dt] for rect, left in self.temp_platforms if left - dt > 0]

        remaining_coins = []
        for coin in self.coins:
            if self.player.rect.colliderect(coin):
                self.level_coins += 1
            else:
                remaining_coins.append(coin)
        self.coins = remaining_coins

        if self.player.rect.colliderect(self.goal):
            self.banked_coins += self.level_coins
            self.level_coins = 0
            if self.level_index == len(LEVELS) - 1:
                self.completed = True
                self.state = "RESULT"
                self.submit_result()
            else:
                self.level_index += 1
                self.load_level()
        elif self.player.rect.top > H or self.level_elapsed > LEVEL_TIME:
            self.message = "Try again!"
            self.message_timer = 1.2
            self.load_level()

    
    def submit_result(self):
        if self.saved_result:
            return

        payload = {
            "nickname": self.nickname,
            "total_time": round(self.run_time, 2),
            "coins": self.total_coins,
            "skin": self.selected_skin_id,
            "played_on": datetime.now().strftime("%Y-%m-%d"),
        }

        try:
            response = requests.post(
                SCORES_URL,
                json=payload,
                timeout=3
            )
            response.raise_for_status()

            self.saved_result = True
            self.leaderboard = self.fetch_leaderboard()
            print("Result successfully saved!")

        except requests.RequestException as error:
            print("Failed to save result:", error)


    # ------------------------------------------------------------------ input

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def go_to_menu(self):
        self.state = "MENU"
        self.name_entry_active = False
        self.name_buffer = self.nickname

    def activate_menu_item(self):
        action = self.menu_items[self.menu_index]
        if action == "Start":
            self.begin_name_entry()
        elif action == "Leaderboard":
            self.leaderboard = self.fetch_leaderboard()
            self.state = "LEADERBOARD"
        elif action == "Choose Skin":
            self.selected_skin_index = next(
                (i for i, s in enumerate(SKINS) if s["id"] == self.selected_skin_id), 0
            )
            self.state = "CHARACTER_SELECT"
        elif action == "Quit":
            self.quit_game()

    def equip_skin(self, index):
        self.selected_skin_index = index
        self.selected_skin_id = SKINS[index]["id"]
        self.save_settings()
        self.state = "MENU"

    def handle_keydown(self, key, text=""):
        if self.state == "MENU":
            if self.name_entry_active:
                self.handle_name_entry(key, text)
                return
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.activate_menu_item()
            return

        if self.state == "CHARACTER_SELECT":
            if key in (pygame.K_UP, pygame.K_w):
                self.selected_skin_index = (self.selected_skin_index - 1) % len(SKINS)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.selected_skin_index = (self.selected_skin_index + 1) % len(SKINS)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.equip_skin(self.selected_skin_index)
            elif key == pygame.K_ESCAPE:
                self.state = "MENU"
            return

        if self.state == "LEADERBOARD":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "MENU"
            return

        if self.state == "RESULT":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_r, pygame.K_ESCAPE):
                self.go_to_menu()
            return

        if self.state == "PLAYING":
            if key == pygame.K_e:
                self.create_platform()
            elif key == pygame.K_SPACE and self.player.on_ground:
                self.player.jump_charge = 0.01
            elif key == pygame.K_ESCAPE:
                self.menu_index = 0
                self.go_to_menu()

    def handle_name_entry(self, key, text):
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_run()
        elif key == pygame.K_ESCAPE:
            self.name_entry_active = False
            self.name_error = ""
        elif key == pygame.K_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]
        elif text and len(self.name_buffer) < 16:
            # event.unicode gives the correct case (uppercase letters, etc.)
            character = "_" if text == " " else text
            if character.isascii() and (character.isalnum() or character == "_"):
                self.name_buffer += character

    def handle_keyup(self, key):
        if self.state == "PLAYING" and key == pygame.K_SPACE:
            self.player.release_jump()

    # ------------------------------------------------------------------ mouse

    def menu_button_rect(self, index):
        return pygame.Rect(W // 2 - 150, 230 + index * 80, 300, 56)

    def name_panel_rect(self):
        return pygame.Rect(W // 2 - 260, 548, 520, 140)

    def skin_card_rect(self, index):
        return pygame.Rect(W // 2 - 230, 170 + index * 140, 460, 110)

    def to_canvas(self, pos):
        """Window mouse coordinates -> game field coordinates."""
        return (
            (pos[0] - self.view_offset[0]) / self.view_scale,
            (pos[1] - self.view_offset[1]) / self.view_scale,
        )

    def handle_mouse_motion(self, pos):
        point = self.to_canvas(pos)
        if self.state == "MENU" and not self.name_entry_active:
            for index in range(len(self.menu_items)):
                if self.menu_button_rect(index).collidepoint(point):
                    self.menu_index = index
        elif self.state == "CHARACTER_SELECT":
            for index in range(len(SKINS)):
                if self.skin_card_rect(index).collidepoint(point):
                    self.selected_skin_index = index

    def handle_mouse_click(self, pos):
        point = self.to_canvas(pos)
        if self.state == "MENU":
            if self.name_entry_active:
                # a click inside the nickname panel does nothing; a click outside closes it
                if self.name_panel_rect().collidepoint(point):
                    return
                self.name_entry_active = False
                self.name_error = ""
            for index in range(len(self.menu_items)):
                if self.menu_button_rect(index).collidepoint(point):
                    self.menu_index = index
                    self.activate_menu_item()
                    return
        elif self.state == "CHARACTER_SELECT":
            for index in range(len(SKINS)):
                if self.skin_card_rect(index).collidepoint(point):
                    self.equip_skin(index)
                    return
        elif self.state == "LEADERBOARD":
            self.state = "MENU"
        elif self.state == "RESULT":
            self.go_to_menu()

    # ------------------------------------------------------------------ drawing

    def draw_text(self, text, position, font=None, color=TEXT, anchor="topleft"):
        image = (font or self.font).render(text, True, color)
        self.canvas.blit(image, image.get_rect(**{anchor: position}))
        return image.get_width()

    def draw_box(self, name, rect):
        self.canvas.blit(self.assets.nine_slice(name, rect.size), rect.topleft)

    def preview_frame(self, skin, running):
        frames = self.assets.skin_frames(skin, 4)
        spec = skin["animations"]["run" if running else "idle"]
        step = int(self.anim_time / spec["frame_time"]) % len(spec["frames"])
        return frames[spec["frames"][step]][0]

    def draw_menu(self):
        self.canvas.blit(self.assets.background, (0, 0))
        self.draw_text("PHASE SHIFT", (W // 2, 130), font=self.big_font, anchor="center")

        for index, label in enumerate(self.menu_items):
            button = self.menu_button_rect(index)
            is_active = index == self.menu_index and not self.name_entry_active
            self.draw_box("button_active" if is_active else "button", button)
            self.draw_text(label, button.center, color=(8, 14, 28) if is_active else TEXT, anchor="center")

        self.draw_text(
            "Mouse or Up/Down + Enter   |   In game: arrows/A,D move, hold Space to charge a jump, E builds a platform",
            (W // 2, H - 14), font=self.small_font, color=ACCENT, anchor="midbottom",
        )

        if self.name_entry_active:
            panel = self.name_panel_rect()
            self.draw_box("panel", panel)
            self.draw_text("Nickname  (Enter - start, Esc - cancel)", (panel.x + 24, panel.y + 16), font=self.small_font, color=ACCENT)
            input_box = pygame.Rect(panel.x + 24, panel.y + 48, panel.width - 48, 44)
            self.draw_box("input", input_box)
            width = self.draw_text(self.name_buffer, (input_box.x + 16, input_box.centery), anchor="midleft")
            if int(self.anim_time * 2) % 2 == 0:  # blinking caret
                caret_x = input_box.x + 16 + width + 3
                pygame.draw.rect(self.canvas, ACCENT, (caret_x, input_box.centery - 12, 3, 24))
            if self.name_error:
                self.draw_text(self.name_error, (panel.x + 24, panel.y + 104), font=self.small_font, color=ERROR)

    def draw_character_select(self):
        self.canvas.blit(self.assets.background, (0, 0))
        self.draw_text("Choose your skin", (W // 2, 90), font=self.big_font, anchor="center")
        for index, skin in enumerate(SKINS):
            card = self.skin_card_rect(index)
            is_cursor = index == self.selected_skin_index
            is_equipped = skin["id"] == self.selected_skin_id
            self.draw_box("button_active" if is_cursor else "panel", card)
            text_color = (8, 14, 28) if is_cursor else TEXT
            preview = self.preview_frame(skin, running=is_cursor)
            self.canvas.blit(preview, preview.get_rect(midleft=(card.x + 28, card.centery)))
            self.draw_text(skin["name"], (card.x + 120, card.y + 30), color=text_color)
            if is_equipped:
                label_color = (90, 60, 0) if is_cursor else COIN
                self.draw_text("EQUIPPED", (card.x + 120, card.y + 66), font=self.small_font, color=label_color)
        self.draw_text("Up/Down or mouse - choose, Enter or click - equip, Esc - back", (W // 2, H - 30), font=self.small_font, color=ACCENT, anchor="center")

    def draw_leaderboard(self):
        self.canvas.blit(self.assets.background, (0, 0))
        self.draw_text("Leaderboard", (W // 2, 70), font=self.big_font, anchor="center")
        panel = pygame.Rect(160, 130, W - 320, H - 200)
        self.draw_box("panel", panel)

        columns = (("#", 200), ("Name", 260), ("Time", 600), ("Coins", 780), ("Skin", 930))
        for label, x in columns:
            self.draw_text(label, (x, 160), color=ACCENT)

        if not self.leaderboard:
            self.draw_text("No runs yet. Finish a run to appear on the board.", (panel.centerx, panel.centery), anchor="center")
        else:
            for index, row in enumerate(self.leaderboard):
                y = 208 + index * 42
                color = MEDALS[index] if index < len(MEDALS) else TEXT
                values = (str(index + 1), row["nickname"], f"{row['total_time']:.2f}s", str(row["coins"]), row["skin"])
                for (_, x), value in zip(columns, values):
                    self.draw_text(value, (x, y), color=color)

        self.draw_text("Press Esc, Enter or click to return", (W // 2, H - 30), font=self.small_font, color=ACCENT, anchor="center")

    def draw_gameplay(self):
        self.canvas.blit(self.assets.background, (0, 0))
        for block in self.platforms:
            self.canvas.blit(self.assets.platform(block.width, block.height), block.topleft)
        for block, left in self.temp_platforms:
            if left < 0.9 and int(left * 10) % 2 == 0:  # blinks before disappearing
                continue
            self.canvas.blit(self.assets.platform(block.width, block.height, tinted=True), block.topleft)
        for pad in self.pads:
            self.canvas.blit(self.assets.sized("environment/pad.png", pad.size), pad.topleft)
        coin_frame = self.assets.coin_frames[int(self.anim_time * 8) % len(self.assets.coin_frames)]
        for coin in self.coins:
            self.canvas.blit(coin_frame, coin_frame.get_rect(center=coin.center))
        self.canvas.blit(self.assets.sized("environment/goal.png", self.goal.size), self.goal.topleft)
        self.player.draw(self.canvas)

        pygame.draw.rect(self.canvas, PANEL, pygame.Rect(0, 0, W, HUD_HEIGHT))
        pygame.draw.line(self.canvas, ACCENT, (0, HUD_HEIGHT), (W, HUD_HEIGHT), 2)
        mid = HUD_HEIGHT // 2
        remaining = max(0, LEVEL_TIME - int(self.level_elapsed))
        self.draw_text(LEVELS[self.level_index]["name"], (20, mid), anchor="midleft")
        self.draw_text(f"Run: {self.run_time:.1f}s", (560, mid), anchor="midleft")
        self.canvas.blit(self.assets.coin_frames[0], self.assets.coin_frames[0].get_rect(midleft=(820, mid)))
        self.draw_text(f"x {self.total_coins}", (846, mid), anchor="midleft", color=COIN)
        self.draw_text(f"Time left: {remaining:02d}s", (W - 20, mid), anchor="midright")

        if self.player.jump_charge:
            fraction = min(1.0, self.player.jump_charge / MAX_JUMP_CHARGE)
            pygame.draw.rect(self.canvas, (10, 15, 25), (20, HUD_HEIGHT + 14, 200, 12), border_radius=4)
            pygame.draw.rect(self.canvas, COIN, (20, HUD_HEIGHT + 14, int(200 * fraction), 12), border_radius=4)

        if self.message_timer:
            self.draw_text(self.message, (W // 2, H - 36), color=(255, 185, 184), anchor="center")

    def draw_result(self):
        self.canvas.blit(self.assets.background, (0, 0))
        panel = pygame.Rect(W // 2 - 340, 110, 680, 500)
        self.draw_box("panel", panel)
        self.draw_text("RESULT", (panel.centerx, 190), font=self.big_font, anchor="center")
        self.draw_text(f"Nickname: {self.nickname}", (panel.x + 70, 270))
        self.draw_text(f"Total time: {self.run_time:.2f}s", (panel.x + 70, 330))
        self.draw_text(f"Coins: {self.total_coins}", (panel.x + 70, 390))
        self.draw_text(f"Skin: {self.current_skin()['name']}", (panel.x + 70, 450))
        preview = self.preview_frame(self.current_skin(), running=False)
        self.canvas.blit(preview, preview.get_rect(midright=(panel.right - 70, 360)))
        self.draw_text("Press Enter or click to return to the menu", (panel.centerx, 560), color=ACCENT, anchor="center")

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "CHARACTER_SELECT":
            self.draw_character_select()
        elif self.state == "LEADERBOARD":
            self.draw_leaderboard()
        elif self.state == "PLAYING":
            self.draw_gameplay()
        elif self.state == "RESULT":
            self.draw_result()
        self.present()

    def present(self):
        """Scales the game field to the window, preserving the aspect ratio."""
        win_w, win_h = self.window.get_size()
        scale = min(win_w / W, win_h / H)
        size = (max(1, int(W * scale)), max(1, int(H * scale)))
        scaled = pygame.transform.scale(self.canvas, size) if size == (W, H) else pygame.transform.smoothscale(self.canvas, size)
        self.view_scale = scale
        self.view_offset = ((win_w - size[0]) // 2, (win_h - size[1]) // 2)
        self.window.fill((0, 0, 0))
        self.window.blit(scaled, self.view_offset)
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            self.anim_time += dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key, event.unicode)
                elif event.type == pygame.KEYUP:
                    self.handle_keyup(event.key)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_click(event.pos)
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()
