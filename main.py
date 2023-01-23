from abc import abstractmethod
from typing import Literal, Union, Sequence, Callable, Optional
from random import randint, uniform, choice

import pygame

FPS = 60

GAME_WIDTH = 800
GAME_HEIGHT = 600

COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (16, 16, 16)
TEXTS = [
    r"I had a grandmother who had been diagnosed with serious paranoid schizophrenia, who everyone said was mentally weak.",
    r"my father said any emotional weakness would bring on symptoms not unlike those dramatically thwarted in The Exorcist.",
    r"'Ghosts use any opportunity to possess you, okay? Don’t be weak, or it’s game over for you.'",
    r"The more vulnerable emotions, such as sadness, fear, and even affection, were seen as threats”",
    r"In our family, crying was considered contagious; it made you extremely vulnerable to the Woo-Woo ghosts",
    r"your mom is just like Poh-Poh, nervous about everything",
    r"we had to be emotionally strong if we didn’t want the ghosts to take our parents away",
    r"'People who cry become Woo-Woo.'",
    r"'These kinds of doctors don’t believe in ghosts'"
]


class KeyMovable:
    @abstractmethod
    def key_move(self, keys: Sequence[bool]):
        pass


class Movable:
    @abstractmethod
    def move(self):
        pass


class Drawable:
    @abstractmethod
    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType]):
        pass


class Collidable:
    @abstractmethod
    def is_colliding(self, other: 'Collidable', on_collision: Callable[['Collidable', 'Collidable'], None]):
        pass

    @property
    @abstractmethod
    def hitbox(self):
        pass


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __repr__(self):
        return f"Vector(x={self.x}, y={self.y})"

    def get_x_vector(self):
        return Vector(self.x, 0)

    def get_y_vector(self):
        return Vector(0, self.y)

    def get_vector_as_tuple(self):
        return self.x, self.y

    def set_x_vector(self, x: float):
        self.x = x

    def set_y_vector(self, y: float):
        self.y = y


class Sprite:

    def __init__(self, path: str, dimensions: Optional[tuple[int, int, int, int]] = None):
        self.path = path
        self.dimensions = pygame.rect.Rect(dimensions) if dimensions else None
        self.image = pygame.image.load(self.path)

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType], x: int, y: int, invert: bool = False):
        image = self.image.subsurface(self.dimensions)
        image = image if not invert else pygame.transform.flip(image, True, False)
        image = pygame.transform.scale(image, (48, 48))
        if self.dimensions:
            game_window.blit(image, (x, y))
        else:
            game_window.blit(image, (x, y))


class SpriteCycle:
    def __init__(self, sprites: list[Sprite], interval: float):
        def interval_end():
            self.sprite_index = (self.sprite_index + 1) % len(self.sprites)

            self.interval_timer = Timer(interval, interval_end)

        self.sprites = sprites
        self.sprite_index = 0
        self.interval_timer = Timer(interval, interval_end)

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType], x: int, y: int, inverted: bool = False):
        if inverted:
            self.sprites[self.sprite_index].draw(game_window, x, y, inverted)
        else:
            self.sprites[self.sprite_index].draw(game_window, x, y)


class SpriteSheet:

    DEFAULT_TIME = 0.1

    def __init__(self, path: str, sprite_x: int, sprite_y: int, *, images_per_row: list[int], cycle_names: list[str],
                 cycle_times:
                 Optional[list[float]] = None):
        self.path = path
        self.sprite_x = sprite_x
        self.sprite_y = sprite_y
        self.images_per_row = images_per_row
        self.image = pygame.image.load(self.path)
        x, y = self.image.get_size()

        if not cycle_times:
            cycle_times = [self.DEFAULT_TIME] * len(cycle_names)

        self.sprites: dict[str, SpriteCycle] = {}

        for i in range(y // self.sprite_y):
            sprites = []
            for j in range(images_per_row[i]):
                sprite = Sprite(self.path, (j * self.sprite_x, i * self.sprite_y, sprite_x, sprite_y))
                sprites.append(sprite)
                print((j * self.sprite_x, i * self.sprite_y, sprite_x, sprite_y))

            self.sprites[cycle_names[i]] = SpriteCycle(sprites, cycle_times[i])

    def get_image_cycle(self, cycle_name: str):
        return self.sprites[cycle_name]


class Player(Movable, KeyMovable, Drawable, Collidable):
    MAX_SPEED = 3
    WIDTH = 48
    HEIGHT = 48
    FRICTION_VECTOR = Vector(0.05, 0.05)

    def __init__(self, x: float, y: float, acceleration_vector: Vector):
        self.x = x
        self.y = y
        self.acceleration_vector = acceleration_vector
        self.velocity_vector = Vector(0, 0)
        self._hitbox = pygame.rect.Rect(int(self.x - self.WIDTH / 2), int(self.y - self.HEIGHT / 2), self.WIDTH,
                                        self.HEIGHT)
        self.sight = 0
        self.show_sight = False
        self.is_playing_animation = True
        self.state: Union[Literal["still"], Literal["moving"]] = "still"

        self.sprites = SpriteSheet("./images/character.png", 32, 32,
                                   images_per_row=[2, 2, 4, 8, 6, 8, 3, 8, 8],
                                   cycle_names=["stand", "blink", "walk", "sprint", "crouch", "jump", "fade", "death",
                                                "attack"],
                                   cycle_times=[1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
                                   )

    def key_move(self, keys: Sequence[bool]):
        if keys[pygame.K_w]:
            self.velocity_vector -= self.acceleration_vector.get_y_vector()

        if keys[pygame.K_s]:
            self.velocity_vector += self.acceleration_vector.get_y_vector()

        if keys[pygame.K_a]:
            self.velocity_vector -= self.acceleration_vector.get_x_vector()

        if keys[pygame.K_d]:
            self.velocity_vector += self.acceleration_vector.get_x_vector()

        velocity_x, velocity_y = self.velocity_vector.get_vector_as_tuple()

        if velocity_x > self.MAX_SPEED:
            self.velocity_vector.set_x_vector(self.MAX_SPEED)

        if velocity_x < -self.MAX_SPEED:
            self.velocity_vector.set_x_vector(-self.MAX_SPEED)

        if velocity_y > self.MAX_SPEED:
            self.velocity_vector.set_y_vector(self.MAX_SPEED)

        if velocity_y < -self.MAX_SPEED:
            self.velocity_vector.set_y_vector(-self.MAX_SPEED)

        if velocity_x > 0:
            self.velocity_vector -= self.FRICTION_VECTOR.get_x_vector()

        if velocity_y > 0:
            self.velocity_vector -= self.FRICTION_VECTOR.get_y_vector()

        if velocity_x < 0:
            self.velocity_vector += self.FRICTION_VECTOR.get_x_vector()

        if velocity_y < 0:
            self.velocity_vector += self.FRICTION_VECTOR.get_y_vector()

        if -0.05 < self.velocity_vector.x < 0.05:
            self.velocity_vector.set_x_vector(0)

        if -0.05 < self.velocity_vector.y < 0.05:
            self.velocity_vector.set_y_vector(0)

        self.state = "still"

        if velocity_x != 0 or velocity_y != 0:
            self.state = "moving"

    def move(self):
        velocity_x, velocity_y = self.velocity_vector.get_vector_as_tuple()

        self.x += velocity_x
        self.y += velocity_y

        if self.x < self.WIDTH / 2:
            self.x = self.WIDTH / 2

        if self.x > GAME_WIDTH - self.WIDTH / 2:
            self.x = GAME_WIDTH - self.WIDTH / 2

        if self.y < self.HEIGHT / 2:
            self.y = self.HEIGHT / 2

        if self.y > GAME_HEIGHT - self.HEIGHT / 2:
            self.y = GAME_HEIGHT - self.HEIGHT / 2

        self._hitbox = pygame.rect.Rect(int(self.x - self.WIDTH / 2), int(self.y - self.HEIGHT / 2), self.WIDTH,
                                        self.HEIGHT)

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType]):
        for cycle in self.sprites.sprites.values():
            cycle.interval_timer.tick()

        clip_area = pygame.rect.Rect(0, 0, GAME_WIDTH, GAME_HEIGHT)
        game_window.set_clip(clip_area)

        if self.show_sight:
            pygame.draw.circle(game_window, COLOR_WHITE, (self.x, self.y), self.sight * GAME_WIDTH / 2)
        else:
            pygame.draw.circle(game_window, COLOR_GRAY, (self.x, self.y), self.sight * GAME_WIDTH / 2)

        game_window.set_clip(None)

        # pygame.draw.rect(game_window, COLOR_RED, self.hitbox)

        if self.sight < 1 and self.is_playing_animation:
            self.sight += 0.02
        elif self.sight >= 1 and self.is_playing_animation:
            self.sight = 1
            self.is_playing_animation = False

        invert = False

        if self.velocity_vector.x < 0:
            invert = True

        image_cycle = None

        if self.state == "moving":
            image_cycle = "sprint"

        if self.state == "still":
            image_cycle = "stand"

        if image_cycle:
            self.sprites.get_image_cycle(image_cycle).draw(game_window, int(self.x - self.WIDTH / 2),
                                                           int(self.y - self.HEIGHT / 2), invert)

    def is_colliding(self, other: 'Collidable', on_collision: Callable[['Collidable', 'Collidable'], None]):
        if self.hitbox.colliderect(other.hitbox):
            on_collision(self, other)

    @property
    def hitbox(self):
        return self._hitbox


class TextBullet(Movable, Drawable, Collidable):
    def __init__(self, y: int, text: str, movement_vector: Vector):
        self.y = y
        self.text = text
        self.movement_vector = movement_vector
        self.text_render = pygame.font.SysFont("Arial", 12).render(self.text, True, COLOR_WHITE)
        self.x = -(self.text_render.get_size()[0] / 2)
        text_width, text_height = self.text_render.get_size()
        self._hitbox = pygame.rect.Rect(int(self.x - text_width / 2), int(self.y - text_height / 2), text_width,
                                        text_height)

    def move(self):
        velocity_x, velocity_y = self.movement_vector.get_vector_as_tuple()

        self.x += velocity_x
        self.y += velocity_y

        text_width, text_height = self.text_render.get_size()
        self._hitbox = pygame.rect.Rect(int(self.x - text_width / 2), int(self.y - text_height / 2), text_width,
                                        text_height)

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType]):
        game_window.blit(self.text_render, self.hitbox)

    def is_colliding(self, other: 'Collidable', on_collision: Callable[['Collidable', 'Collidable'], None]):
        if self.hitbox.colliderect(other.hitbox):
            on_collision(self, other)

    @property
    def hitbox(self):
        return self._hitbox


class Timer(Drawable):
    PADDING = 20

    def __init__(self, time: float, on_end: Callable[..., None], position: Optional[tuple[int, int]] = None):
        self.time = time
        self.on_end = on_end
        self.position = position
        self.font = pygame.font.Font("./fonts/clock.ttf", 72)
        self.rendered_text = self.font.render(str(self.time), True, COLOR_RED)
        self.fps_clock = pygame.time.Clock()
        self.time_elapsed = 0

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType]):
        text_width, text_height = self.rendered_text.get_size()
        position = self.position if self.position is not None else (
            GAME_WIDTH - text_width - self.PADDING, self.PADDING)

        game_window.blit(self.rendered_text, position)

    def tick(self):
        if self.time > 0:
            time = self.fps_clock.tick(FPS)
            self.time -= time / 1000

        self.rendered_text = self.font.render(str(round(self.time, 1)), True, COLOR_RED)

        if self.time <= 0:
            self.on_end()


class Stopwatch(Drawable):
    PADDING = 20

    def __init__(self, time: float = 0, position: Optional[tuple[int, int]] = None):
        self.time = time
        self.position = position
        self.font = pygame.font.Font("./fonts/clock.ttf", 72)
        self.rendered_text = self.font.render(str(self.time), True, COLOR_RED)
        self.fps_clock = pygame.time.Clock()
        self.time_elapsed = 0

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType]):
        text_width, text_height = self.rendered_text.get_size()
        position = self.position if self.position is not None else (
            GAME_WIDTH - text_width - self.PADDING, self.PADDING)

        game_window.blit(self.rendered_text, position)

    def tick(self):
        time = self.fps_clock.tick(FPS)
        self.time += time / 1000

        self.rendered_text = self.font.render(str(round(self.time, 1)), True, COLOR_RED)


class Wall(Drawable, Collidable):
    def __init__(self, x: int, y: int, width: int, height: int, *, debug=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._hitbox = pygame.rect.Rect(self.x, self.y, self.width, self.height)
        self.debug = debug

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType]):
        if self.debug:
            pygame.draw.rect(game_window, COLOR_RED, self.hitbox)
        else:
            pygame.draw.rect(game_window, COLOR_BLACK, self.hitbox)

    def is_colliding(self, other: 'Collidable', on_collision: Callable[['Collidable', 'Collidable'], None]):
        if self.hitbox.colliderect(other):
            on_collision(self, other)

    @property
    def hitbox(self):
        return self._hitbox


class EndZone(Collidable):
    def __init__(self, x: int, y: int, width: int, height: int, *, debug=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._hitbox = pygame.rect.Rect(self.x, self.y, self.width, self.height)
        self.debug = debug

    def draw(self, game_window: Union[pygame.Surface, pygame.SurfaceType]):
        if self.debug:
            pygame.draw.rect(game_window, COLOR_RED, self.hitbox)
        else:
            pygame.draw.rect(game_window, COLOR_BLACK, self.hitbox)

    def is_colliding(self, other: 'Collidable', on_collision: Callable[['Collidable', 'Collidable'], None]):
        if self.hitbox.colliderect(other):
            on_collision(self, other)

    @property
    def hitbox(self):
        return self._hitbox


def check_quit(keys: Sequence[bool]) -> bool:
    # ESC key and QUIT button
    if keys[pygame.K_ESCAPE]:
        return True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True

    # returns false otherwise
    return False


def main():
    pygame.init()

    game_window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))

    game_state: Union[Literal[1], Literal[2], None] = 1

    player = Player(200, 200, Vector(0.25, 0.25))

    def change_state():
        nonlocal game_state
        game_state = 2

        on_state_change()

    def spawn_bullet():
        nonlocal bullet_timer

        b = TextBullet(randint(20, GAME_HEIGHT - 20), choice(TEXTS), Vector(uniform(1.5, 2.5), 0))

        bullets.append(b)
        drawables.append(b)
        movables.append(b)

        bullet_timer = Timer(0.25, spawn_bullet)

    def on_player_bullet_collide(user: Player, bullet: TextBullet):
        bullets.remove(bullet)
        movables.remove(bullet)
        drawables.remove(bullet)

        if user.sight >= 0.1:
            user.sight -= 0.05

    def on_player_wall_collide(user: Player, wall: Wall):
        user.x = user.y = 50
        user.velocity_vector = Vector(0, 0)

    def on_player_end_collide(user: Player, wall: Wall):
        nonlocal game_state
        game_state = 3

    timer = Timer(20, change_state)

    def on_state_change():
        nonlocal timer, bullets, drawables, movables, walls
        timer = Stopwatch()

        player.show_sight = True

        bullets.clear()
        drawables = [player, *walls, end_zone, timer]
        movables = [player]

        player.x = player.y = 50

    end_zone = EndZone(600, 520, 80, 140)
    bullets: list[TextBullet] = []
    drawables: list[Drawable] = [player, timer]
    movables: list[Movable] = [player]
    walls: list[Wall] = [
        Wall(0, 100, 200, 20),
        Wall(200, 100, 20, 100),
        Wall(120, 200, 100, 20),
        Wall(300, 100, 200, 20),
        Wall(300, 180, 200, 20),
        Wall(300, 180, 20, 120),
        Wall(500, 100, 20, 100),
        Wall(600, 100, 200, 20),
        Wall(40, 100, 20, 120),
        Wall(0, 280, 220, 20),
        Wall(100, 380, 220, 20),
        Wall(100, 380, 20, 100),
        Wall(100, 480, 100, 20),
        Wall(0, 380, 40, 20),
        Wall(0, 450, 40, 20),
        Wall(100, 560, 20, 100),
        Wall(100, 560, 100, 20),
        Wall(100, 560, 100, 20),
        Wall(300, 400, 20, 120),
        Wall(380, 480, 20, 120),
        Wall(460, 380, 20, 220),
        Wall(300, 380, 180, 20),
        Wall(300, 280, 180, 20),
        Wall(500, 180, 240, 20),
        Wall(500, 180, 240, 20),
        Wall(580, 180, 20, 140),
        Wall(580, 180, 20, 180),
        Wall(680, 260, 140, 20),
        Wall(580, 340, 100, 20),
        Wall(580, 440, 100, 20),
        Wall(580, 440, 20, 180),
        Wall(680, 340, 20, 120),
        Wall(680, 520, 20, 140),
    ]

    bullet_timer = Timer(2, spawn_bullet)

    while game_state is not None:
        keys = pygame.key.get_pressed()

        game_window.fill(COLOR_BLACK)

        pygame.event.clear()

        # --- code ---
        if check_quit(keys):
            game_state = None

        timer.tick()

        if game_state == 1:
            bullet_timer.tick()

        if game_state == 2:
            for wall in walls:
                player.is_colliding(wall, on_player_wall_collide)

        player.key_move(keys)

        for moveable in movables:
            moveable.move()

        for drawable in drawables:
            drawable.draw(game_window)

        for bullet in bullets:
            player.is_colliding(bullet, on_player_bullet_collide)

        if game_state == 2:
            player.is_colliding(end_zone, on_player_end_collide)

        if game_state == 3:
            print("End")
            game_state = None

        pygame.display.update()


if __name__ == "__main__":
    main()
