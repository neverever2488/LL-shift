"""Vienkārša Pygame platformera spēle ar uzlādējamu lēcienu un pagaidu platformām."""

import sys
import pygame


WIDTH, HEIGHT = 960, 600
FPS = 60
PLAYER_SIZE = 34
GRAVITY = 0.62
MAX_FALL_SPEED = 14
LEVEL_TIME = 90

BG = (20, 28, 45)
TEXT = (239, 244, 255)
PLATFORM = (77, 132, 188)
PLAYER = (247, 180, 70)
COIN = (255, 220, 74)
GOAL = (92, 221, 146)
PAD = (242, 104, 119)
TEMP = (171, 119, 243)


# Katram līmenim norāda sākuma vietu, platformas, monētas, atsperes un finišu.
LEVELS = [
    {
        "name": "Level 1 - First Steps",
        "spawn": (70, 480),
        "platforms": [(0, 550, 260, 50), (325, 485, 160, 20), (550, 415, 160, 20),
                      (775, 345, 150, 20)],
        "coins": [(390, 440), (615, 370), (840, 300)],
        "pads": [], "goal": (865, 275, 35, 70),
    },
    {
        "name": "Level 2 - Spring Trail",
        "spawn": (55, 480),
        "platforms": [(0, 550, 190, 50), (255, 490, 100, 20), (425, 425, 110, 20),
                      (620, 350, 105, 20), (800, 270, 120, 20)],
        "coins": [(290, 445), (475, 380), (670, 305), (850, 225)],
        "pads": [(120, 530, 45, 20)], "goal": (855, 200, 35, 70),
    },
    {
        "name": "Level 3 - Build Your Path",
        "spawn": (45, 480),
        "platforms": [(0, 550, 180, 50), (290, 460, 100, 20), (500, 365, 95, 20),
                      (735, 260, 170, 20)],
        "coins": [(325, 415), (540, 320), (680, 400), (810, 215)],
        "pads": [(120, 530, 45, 20)], "goal": (845, 190, 35, 70),
    },
    {
        "name": "Level 4 - Final Run",
        "spawn": (35, 480),
        "platforms": [(0, 550, 150, 50), (230, 500, 80, 20), (405, 425, 85, 20),
                      (605, 330, 85, 20), (805, 215, 115, 20)],
        "coins": [(265, 455), (445, 380), (645, 285), (755, 365), (855, 170)],
        "pads": [(95, 530, 40, 20), (430, 405, 35, 20)], "goal": (855, 145, 35, 70),
    },
]


class Player:
    def __init__(self, pos):
        self.rect = pygame.Rect(*pos, PLAYER_SIZE, PLAYER_SIZE)
        self.velocity = pygame.Vector2()
        self.on_ground = False
        self.jump_charge = 0
        self.facing = 1

    def update(self, keys, platforms):
        direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.velocity.x = direction * 5
        if direction:
            self.facing = direction

        self.rect.x += round(self.velocity.x)
        for block in platforms:
            if self.rect.colliderect(block):
                if self.velocity.x > 0:
                    self.rect.right = block.left
                elif self.velocity.x < 0:
                    self.rect.left = block.right

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


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Phase Shift")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.big_font = pygame.font.Font(None, 62)
        self.level_index = 0
        self.total_coins = 0
        self.completed = False
        self.load_level()

    def load_level(self):
        data = LEVELS[self.level_index]
        self.player = Player(data["spawn"])
        self.platforms = [pygame.Rect(item) for item in data["platforms"]]
        self.coins = [pygame.Rect(x - 9, y - 9, 18, 18) for x, y in data["coins"]]
        self.pads = [pygame.Rect(item) for item in data["pads"]]
        self.goal = pygame.Rect(data["goal"])
        self.temp_platforms = []  # [taisnstūris, atlikušais laiks]
        self.elapsed = 0.0
        self.message = ""
        self.message_timer = 0.0

    def create_platform(self):
        if len(self.temp_platforms) >= 2:
            return
        x = self.player.rect.centerx + self.player.facing * 48 - 42
        y = self.player.rect.bottom + 18
        rect = pygame.Rect(max(0, min(WIDTH - 84, x)), min(HEIGHT - 35, y), 84, 14)
        if not any(rect.colliderect(block) for block in self.platforms):
            self.temp_platforms.append([rect, 2.8])

    def update(self, dt):
        if self.completed:
            return
        self.elapsed += dt
        self.message_timer = max(0, self.message_timer - dt)
        keys = pygame.key.get_pressed()
        blocks = self.platforms + [item[0] for item in self.temp_platforms]
        self.player.update(keys, blocks)

        for pad in self.pads:
            if self.player.rect.colliderect(pad) and self.player.velocity.y >= 0:
                self.player.rect.bottom = pad.top
                self.player.velocity.y = -15

        self.temp_platforms = [[rect, left - dt] for rect, left in self.temp_platforms if left - dt > 0]
        self.coins = [coin for coin in self.coins if not self.collect_coin(coin)]

        if self.player.rect.colliderect(self.goal):
            if self.level_index == len(LEVELS) - 1:
                self.completed = True
            else:
                self.level_index += 1
                self.load_level()
        elif self.player.rect.top > HEIGHT or self.elapsed > LEVEL_TIME:
            self.message = "Try again!"
            self.message_timer = 1.2
            self.load_level()

    def collect_coin(self, coin):
        if self.player.rect.colliderect(coin):
            self.total_coins += 1
            return True
        return False

    def handle_keydown(self, key):
        if self.completed:
            if key == pygame.K_r:
                self.level_index, self.total_coins, self.completed = 0, 0, False
                self.load_level()
            return
        if key == pygame.K_e:
            self.create_platform()
        if key == pygame.K_SPACE and self.player.on_ground:
            self.player.jump_charge = 0.01

    def handle_keyup(self, key):
        if key == pygame.K_SPACE and self.player.jump_charge:
            power = 9 + min(self.player.jump_charge, 0.65) * 9
            self.player.velocity.y = -power
            self.player.on_ground = False
            self.player.jump_charge = 0

    def draw_text(self, text, position, size_font=None, color=TEXT):
        image = (size_font or self.font).render(text, True, color)
        self.screen.blit(image, position)

    def draw(self):
        self.screen.fill(BG)
        data = LEVELS[self.level_index]
        for block in self.platforms:
            pygame.draw.rect(self.screen, PLATFORM, block, border_radius=5)
        for block, life in self.temp_platforms:
            pygame.draw.rect(self.screen, TEMP, block, border_radius=4)
            pygame.draw.rect(self.screen, TEXT, block, 1, border_radius=4)
        for pad in self.pads:
            pygame.draw.rect(self.screen, PAD, pad, border_radius=5)
            pygame.draw.line(self.screen, TEXT, pad.bottomleft, pad.midtop, 2)
            pygame.draw.line(self.screen, TEXT, pad.midtop, pad.bottomright, 2)
        for coin in self.coins:
            pygame.draw.ellipse(self.screen, COIN, coin)
            pygame.draw.ellipse(self.screen, (255, 245, 180), coin.inflate(-8, -4))
        pygame.draw.rect(self.screen, GOAL, self.goal, border_radius=4)
        pygame.draw.polygon(self.screen, TEXT, [(self.goal.x + 8, self.goal.y + 10), (self.goal.x + 8, self.goal.y + 33), (self.goal.right - 6, self.goal.y + 21)])
        pygame.draw.rect(self.screen, PLAYER, self.player.rect, border_radius=7)

        pygame.draw.rect(self.screen, (12, 17, 28), (0, 0, WIDTH, 56))
        remaining = max(0, LEVEL_TIME - int(self.elapsed))
        self.draw_text(data["name"], (16, 16))
        self.draw_text(f"TIME: {remaining:02d}s", (WIDTH - 145, 16))
        self.draw_text(f"COINS: {self.total_coins}", (WIDTH - 300, 16))
        self.draw_text("A/D or Arrows: Move   Hold Space: Charge jump   E: Create platform", (16, HEIGHT - 30), color=(190, 204, 225))
        if self.player.jump_charge:
            pygame.draw.rect(self.screen, (45, 52, 73), (16, 62, 150, 10), border_radius=4)
            pygame.draw.rect(self.screen, COIN, (16, 62, int(150 * min(1, self.player.jump_charge / 0.65)), 10), border_radius=4)
            self.player.jump_charge += 1 / FPS
        if self.completed:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            title = self.big_font.render("YOU WIN!", True, TEXT)
            self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 240)))
            result = self.font.render(f"Coins collected: {self.total_coins}. Press R to play again.", True, TEXT)
            self.screen.blit(result, result.get_rect(center=(WIDTH // 2, 305)))
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                if event.type == pygame.KEYUP:
                    self.handle_keyup(event.key)
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()
