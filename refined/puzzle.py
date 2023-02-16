import os
import random
from random import random, choice

import katagames_engine as kengi


kengi.bootstrap_e()

pygame = kengi.pygame
text = kengi.util.drawtext
scrw, scrh = None, None


def load_image(path: str, scale=1.0, color_key=None):
    img = pygame.image.load(path)
    w, h = img.get_size()
    img = pygame.transform.scale(img, (int(w*scale), int(h*scale)))
    if color_key:
        img.set_colorkey(color_key)
    img.convert()
    return img


# gui
class Button:
    def __init__(self, x=0, y=0, w=100, h=50, label='Button', action=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.action = action
        self.label = label
        self.text = text(self.label, 40, aliased=True)
        self.active_color = (204, 122, 68)
        self.inactive_color = (182, 122, 87)
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.is_active = False

    def update(self, events):
        mx, my = kengi.vscreen.proj_to_vscreen(pygame.mouse.get_pos())

        if self.rect.collidepoint(mx, my):
            self.is_active = True
        else:
            self.is_active = False
        for e in events:
            if e.type == kengi.events.EngineEvTypes.Mousedown:
                if e.button == 1:
                    if self.is_active:
                        if self.action is not None:
                            self.action()

    def draw(self, surf):
        color = self.active_color if self.is_active else self.inactive_color
        pygame.draw.rect(surf, color, (self.x, self.y, self.w, self.h), border_radius=5)
        surf.blit(self.text, self.text.get_rect(center=self.rect.center))


# effets
class Sparkle:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.r = 5
        self.alive = True

    def update(self, events): # list[pygame.event.Event]):
        self.r += 5
        if self.r > 50:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, 'white', (self.x, self.y), self.r, 5)


class Shape:
    def __init__(self, x=0, y=0, shape='a', row=0, col=0, target_pos=None):
        self.x, self.y = x, y
        self.shape = shape
        self.size = 50

        # TODO organize code such that loading of images is done outside of __init__
        self.img = self.get_shape(shape)
        self.bg1 = self.get_shape_bg(shape, 1.1)
        self.bg2 = self.get_shape_bg(shape, 1.2)
        self.row = row
        self.col = col

        if target_pos:
            self.target_x, self.target_y = target_pos
        else:
            self.target_x, self.target_y = x, y

        self.active = True
        self.clicked = False

    def update(self, events):
        dx = (self.target_x - self.x)
        dy = (self.target_y - self.y)
        if abs(dx) > 1:
            self.x += dx / 5
        else:
            self.x = self.target_x
        if abs(dy) > 1:
            self.y += dy / 5
        else:
            self.y = self.target_y

        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx, my):
            self.active = True
        else:
            self.active = False

        for e in events:
            if e.type == kengi.EngineEvTypes.Mousedown:
                if self.active:
                    self.clicked = True
            elif e.type == kengi.EngineEvTypes.Mouseup:
                self.clicked = False

    @property
    def rect(self):
        diff = Puzzle.box_size - max(self.img.get_width(), self.img.get_height())
        return self.img.get_rect(center=(self.x, self.y)).inflate(diff, diff)

    def draw(self, surf):
        # t = text(f'{self.row},{self.col}', 20)
        # self.img = t
        if self.clicked:
            surf.blit(self.bg2, self.bg2.get_rect(center=(self.x, self.y)))
        elif self.active:
            surf.blit(self.bg1, self.bg1.get_rect(center=(self.x, self.y)))
        surf.blit(self.img, self.img.get_rect(center=(self.x, self.y)))
        # pygame.draw.rect(surf, 'white', self.rect, 1)

    def update_target(self, pos):
        self.target_x, self.target_y = pos

    @staticmethod
    def tile(shape):
        shapes = {
            'a': 'green',
            'b': 'yellow',
            'c': 'blue',
            'd': 'red'
        }
        s = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(s, shapes[shape], (25, 25), 10)
        return s

    @staticmethod
    def get_shape(shape):
        return load_image(os.path.join('../img/', f'{shape}.png'), scale=0.4)

    def get_shape_bg(self, shape, scale):
        img = self.get_shape(shape)
        w, h = img.get_size()
        img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
        img.fill('white', special_flags=pygame.BLEND_ADD)
        return img


class Puzzle:
    box_size = 80

    def __init__(self):
        self.cols = 10
        self.rows = 5
        self.x = (scrw - self.box_size * self.cols) // 2
        self.y = (scrh - self.box_size * self.rows) // 2 + 30
        self.shapes = {}
        self.shape1 = None
        self.shape2 = None
        self.last_swapped = None
        self.sparkles = []
        self.active = True
        self.over = False
        self.add_score = 0
        self.score = 0
        self.score_allowed = False
        self.target_score = 100
        self.moves_left = 3
        self.reset_button = Button(scrw // 2 - 100, 25, 200, 50, label='Shuffle', action=self.shuffle)

    def init_puzzle(self):
        grid = [[choice('abcdef') for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.x + c * self.box_size + self.box_size // 2
                y = self.y + r * self.box_size + self.box_size // 2
                self.shapes[(r, c)] = Shape(x, y, grid[r][c], r, c)
                self.pop(r, c, sparkle=False)

    def get_pos(self, row, col):
        col = col
        s = self.box_size
        return self.x + col * s + s // 2, self.y + row * s + s // 2

    def pop(self, row, col, sparkle=True):

        self.shapes.pop((row, col))
        for i in range(row - 1, -1, -1):
            shape = self.shapes[(i, col)]
            shape.row, shape.col = i + 1, col  # update row and column for reference
            shape.update_target(self.get_pos(i + 1, col))  # update target position
            self.shapes[(i + 1, col)] = shape  # update the key in the dictionary

        # add a new shape at position [0, col]
        x, y = self.get_pos(-10, col)
        temp = Shape(x, y, choice('abcdef'), 0, col, target_pos=self.get_pos(0, col))
        temp.x = temp.target_x
        self.shapes[(0, col)] = temp
        if sparkle:
            self.sparkles.append(Sparkle(*self.get_pos(row, col)))

        if self.score_allowed:
            self.add_score += 10

    def check_combinations(self):
        min_combo_length = 3
        all_indexes = []

        # vertical combination checking
        for col in range(self.cols):
            c = 1
            curr_shape = ''
            indexes = []
            for row in range(self.rows):
                shape = self.shapes[(row, col)].shape
                if shape == curr_shape:
                    c += 1
                    indexes.append((row, col))
                else:
                    if c >= min_combo_length:
                        all_indexes.extend(indexes)
                    indexes.clear()
                    indexes.append((row, col))
                    c = 1
                    curr_shape = shape
            if c >= min_combo_length:
                all_indexes.extend(indexes)

        # horizontal combination checking
        for row in range(self.rows):
            c = 1
            curr_shape = ''
            indexes = []
            for col in range(self.cols):
                shape = self.shapes[(row, col)].shape
                if shape == curr_shape:
                    c += 1
                    indexes.append((row, col))
                else:
                    if c >= min_combo_length:
                        all_indexes.extend(indexes)
                    indexes.clear()
                    indexes.append((row, col))
                    c = 1
                    curr_shape = shape
            if c >= min_combo_length:
                all_indexes.extend(indexes)
        return all_indexes

    def switch_shapes(self, pos1, pos2):
        # validate swap [it needs to be only in adjacent shapes excluding diagonals]
        r1, c1 = pos1
        r2, c2 = pos2
        if r1 == r2:
            if c1 not in (c2 - 1, c2 + 1):
                return
        elif c1 == c2:
            if r1 not in (r2 - 1, r2 + 1):
                return
        else:
            return
        shape1 = self.shapes[pos1]
        shape2 = self.shapes[pos2]
        shape1.row, shape2.row = shape2.row, shape1.row
        shape1.col, shape2.col = shape2.col, shape1.col
        self.shapes[pos1], self.shapes[pos2] = shape2, shape1  # switch the actual shapes from the dict
        shape1.update_target(self.get_pos(*pos2))
        shape2.update_target(self.get_pos(*pos1))
        # print(sha, shape2)

    def shuffle(self):
        self.score_allowed = False
        for r in range(self.rows):
            for c in range(self.cols):
                if random() > 0.5:
                    self.pop(r, c)

    def check_swap(self, events):
        for e in events:
            if e.type == kengi.EngineEvTypes.Mousedown:
                if e.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    for _, shape in self.shapes.items():
                        if shape.rect.collidepoint(mx, my):
                            self.shape1 = shape.row, shape.col
            elif e.type == kengi.EngineEvTypes.Mouseup:
                if e.button == 1 and self.shape1:
                    mx, my = e.pos
                    for _, shape in self.shapes.items():
                        if shape.rect.collidepoint(mx, my):
                            self.shape2 = shape.row, shape.col
                else:
                    self.shape1 = None
        if self.shape1 and self.shape2:
            self.switch_shapes(self.shape1, self.shape2)
            self.last_swapped = self.shape1, self.shape2
            self.shape1 = None
            self.shape2 = None

    def check_input(self, events):
        if self.active:
            if self.last_swapped:
                if not self.score_allowed:
                    self.score_allowed = True
                if not self.check_combinations():
                    self.switch_shapes(*self.last_swapped)
                else:
                    self.moves_left -= 1
                self.last_swapped = None
            else:
                for i in self.check_combinations():
                    self.pop(*i)
                self.check_swap(events)

    def update(self, events):
        if self.add_score:
            self.score += 1
            self.add_score -= 1

        self.active = True

        for _, shape in self.shapes.items():
            if shape.x != shape.target_x or shape.y != shape.target_y:
                self.active = False
            shape.update(events)

        if self.active:
            if self.last_swapped:
                if not self.score_allowed:
                    self.score_allowed = True
                if not self.check_combinations():
                    self.switch_shapes(*self.last_swapped)
                else:
                    self.moves_left -= 1
                self.last_swapped = None
            else:
                for i in self.check_combinations():
                    self.pop(*i)
                self.check_swap(events)

        self.sparkles = [i for i in self.sparkles if i.alive]
        for i in self.sparkles:
            i.update(events)

        self.reset_button.update(events)
        if self.moves_left <= 0 or self.score >= self.target_score:
            if self.active and not self.sparkles:
                if not self.check_combinations():
                    if not self.check_swap(events):
                        self.over = True

    def draw(self, surf):
        global scrw
        for i in range(self.rows + 1):
            x = self.x + self.cols * self.box_size
            y = self.y + self.box_size * i
            pygame.draw.line(surf, 'white', (self.x, y), (x, y))
        for i in range(self.cols + 1):
            x = self.x + self.box_size * i
            y = self.y + self.box_size * self.rows
            pygame.draw.line(surf, 'white', (x, self.y), (x, y))
        for _, shape in self.shapes.items():
            shape.draw(surf)
        for i in self.sparkles:
            i.draw(surf)
        # matches = self.check_matches()
        # if matches:
        #     pygame.draw.lines(surf, 'green', False, [self.get_pos(*i) for i in matches])
        pygame.draw.rect(surf, 'black', (0, 0, scrw, 100))
        t = text(f'Goal: {self.target_score}', size=25, aliased=True)
        surf.blit(t, t.get_rect(midright=(scrw - 75, 25)))
        t = text(f'{self.score}', aliased=True)
        surf.blit(t, t.get_rect(midright=(scrw - 75, 75)))
        t = text('Moves Left', size=25, aliased=True)
        surf.blit(t, t.get_rect(midleft=(75, 25)))
        t = text(f'{self.moves_left}', aliased=True)
        surf.blit(t, t.get_rect(midleft=(75, 75)))
        self.reset_button.draw(surf)


class Match3Ticker(kengi.EvListener):
    def __init__(self, refgame):
        super().__init__()
        self.puzzle = Puzzle()
        self.puzzle.init_puzzle()
        self.game = refgame

    def on_update(self, ev):
        self.puzzle.update([ev, ])

    def on_keydown(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self.game.gameover = True

    def on_mousedown(self, ev):
        self.puzzle.update([ev, ])

    def on_mouseup(self, ev):
        self.puzzle.update([ev, ])

    def on_paint(self, ev):
        ev.screen.fill(kengi.pal.japan['navy'])
        self.puzzle.draw(ev.screen)


class Match3Game(kengi.GameTpl):
    def __init__(self):
        super().__init__()
        self.ticker = None

    def init_video(self):
        global scrw, scrh
        kengi.init(1)
        scrw, scrh = kengi.get_surface().get_size()

    def enter(self, vms=None):
        super().enter(vms)
        self.ticker = Match3Ticker(self)
        self.ticker.turn_on()


g = Match3Game()
g.loop()
