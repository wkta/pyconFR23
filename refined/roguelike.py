import katagames_engine as kengi
kengi.bootstrap_e()

"""
this file contains 3 basic mvc COMPOnents
that can implement a rogue-like
"""
import os  # for loading assets
import katagames_engine as kengi


pygame = kengi.pygame
EngineEvTypes = kengi.EngineEvTypes
CogObject = kengi.events.Emitter
ReceiverObj = kengi.events.EvListener
Sprsheet = kengi.gfx.Spritesheet
BoolMatrx = kengi.struct.BoolMatrix


# game-specific declarations
MyEvTypes = kengi.struct.enum(
    'PlayerMoves',  # contains: new_pos
    'NewLevel'
)


# ------------------------------------
#  THE MODEL
# ------------------------------------
class NinjamazeMod(CogObject):
    VISION_RANGE = 4  # cells
    fov_computer = None

    SPELL_PHASING, SPELL_FIREBALL, SPELL_BASH = range(23, 23+3)  # spell codes

    def __init__(self):
        super().__init__()
        self.rm = None
        self.player_pos = None
        self.visibility_m = None

        self.enemies_pos2type = dict()
        # spell casting
        self.equiped_spell = None
        self.owned_spells = set()

        self.reset_level()

    def _update_vision(self, i, j):
        if self.fov_computer is None:
            self.fov_computer = kengi.rogue.FOVCalc()

        self.visibility_m.set_val(i, j, True)

        def func_visibility(a, b):
            if self.visibility_m.is_out(a, b):
                return False
            if self.rm.getMatrix().get_val(a, b) is None:  # cannot see through walls
                return False
            return True

        li_visible = self.fov_computer.calc_visible_cells_from(i, j, self.VISION_RANGE, func_visibility)

        for c in li_visible:
            self.visibility_m.set_val(c[0], c[1], True)

    def reset_level(self):
        w, h = 24, 24
        self.rm = kengi.rogue.RandomMaze(w, h, min_room_size=3, max_room_size=5)
        self.visibility_m = BoolMatrx((w, h))
        self.visibility_m.set_all(False)  # hiding all cells

        # getting a valid initial position for the avatar
        self.player_pos = self.rm.pick_walkable_cell()

        # now, the avatar can see.
        self._update_vision(*self.player_pos)

        self.pev(MyEvTypes.NewLevel)
        self.pev(MyEvTypes.PlayerMoves, new_pos=self.player_pos)

        # enemies generation
        for _ in range(5):
            c = self.rm.pick_walkable_cell()
            self.enemies_pos2type[tuple(c)] = 1  # all enemies type=1

    def can_see(self, cell):
        return self.visibility_m.get_val(*cell)

    def get_terrain(self):
        return self.rm.getMatrix()

    def push_player(self, direction):
        deltas = {
            0: (+1, 0),
            1: (0, -1),
            2: (-1, 0),
            3: (0, +1)
        }
        delta = deltas[direction]
        dest = list(self.player_pos)
        dest[0] += delta[0]
        dest[1] += delta[1]
        t = self.get_terrain()
        if t.is_out(*dest):  # out of bounds
            return
        if t.get_val(*dest) is None:  # wall
            return
        self.player_pos = dest
        self._update_vision(*dest)
        self.pev(MyEvTypes.PlayerMoves, new_pos=dest)

    def get_av_pos(self):
        return self.player_pos


# ------------------------------------
#  THE VIEW
# ------------------------------------
class NinjamazeView(ReceiverObj):
    CELL_SIDE = 32  # px
    WALL_COLOR = (8, 8, 24)
    HIDDEN_CELL_COLOR = (24, 24, 24)

    def __init__(self, ref_mod):
        super().__init__()
        self.assoc_r_col = dict()
        grid_rez = (32, 32)

        img = pygame.image.load(os.path.join('../img', 'tileset.png')).convert()
        self.tileset = Sprsheet(img, 2)  # use upscaling x2
        self.tileset.set_infos(grid_rez)

        img = pygame.image.load(os.path.join('../img', '1.png')).convert()
        self.planche_avatar = Sprsheet(img, 2)  # upscaling x2
        self.planche_avatar.set_infos(grid_rez)
        self.planche_avatar.colorkey = (255, 0, 255)

        self.monster_img = pygame.image.load(os.path.join('../img', 'monster.png')).convert()
        self.monster_img = pygame.transform.scale(self.monster_img, (32, 32))
        self.monster_img.set_colorkey((255, 0, 255))

        self.mod = ref_mod
        self.avatar_apparence = self.planche_avatar.image_by_rank(0)
        self.pos_avatar = ref_mod.get_av_pos()

    def proc_event(self, ev, source):
        if ev.type == EngineEvTypes.PAINT:
            self._draw_content(ev.screen)
        elif ev.type == MyEvTypes.PlayerMoves:
            self.pos_avatar = ev.new_pos

    def _draw_content(self, scr):
        scr.fill(self.WALL_COLOR)

        nw_corner = (0, 0)
        tmp_r4 = [None, None, None, None]

        tuile = self.tileset.image_by_rank(912)

        dim = self.mod.get_terrain().get_size()
        for i in range(dim[0]):
            for j in range(dim[1]):
                # ignoring walls
                tmp = self.mod.get_terrain().get_val(i, j)
                if tmp is None:
                    continue

                tmp_r4[0], tmp_r4[1] = nw_corner
                tmp_r4[0] += i * self.CELL_SIDE
                tmp_r4[1] += j * self.CELL_SIDE
                tmp_r4[2] = tmp_r4[3] = self.CELL_SIDE
                if not self.mod.can_see((i, j)):  # hidden cell
                    pygame.draw.rect(scr, self.HIDDEN_CELL_COLOR, tmp_r4)
                else:  # visible tile
                    scr.blit(tuile, tmp_r4)

        # draw avatar process
        av_i, av_j = self.pos_avatar[0] * self.CELL_SIDE, self.pos_avatar[1] * self.CELL_SIDE
        scr.blit(self.avatar_apparence, (av_i, av_j, 32, 32))

        # draw enemies
        for enemy_info in self.mod.enemies_pos2type.items():
            pos, t = enemy_info
            en_i, en_j = pos[0] * self.CELL_SIDE, pos[1] * self.CELL_SIDE
            scr.blit(self.monster_img, (en_i, en_j, 32, 32))


# ------------------------------------
#  THE CONTROLLER
# ------------------------------------
class NinjamazeCtrl(ReceiverObj):

    def __init__(self, ref_mod):
        super().__init__()
        self.mod = ref_mod

    def proc_event(self, ev, source):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RIGHT:
                self.mod.push_player(0)
            elif ev.key == pygame.K_UP:
                self.mod.push_player(1)
            elif ev.key == pygame.K_LEFT:
                self.mod.push_player(2)
            elif ev.key == pygame.K_DOWN:
                self.mod.push_player(3)
            elif ev.key == pygame.K_SPACE:
                self.mod.reset_level()
            elif ev.key == pygame.K_ESCAPE:
                self.pev(EngineEvTypes.GAMEENDS)


def print_tuto():
    print('\n' + '*'*32)
    print('This example showcases capabilities of the kengi.rogue')
    print('submodule... You can easily generate a RANDOM MAZE')
    print('you can also use a field-of-view generic algorithm')
    print('to simulate the "fog of war"/unknown parts of the map.')
    print('>>CONTROLS<< SPACE to regen maze | ESCAPE to quit\n' + '*'*32)


if __name__ == '__main__':
    kengi.init()
    m = NinjamazeMod()
    NinjamazeView(m).turn_on()
    NinjamazeCtrl(m).turn_on()
    print_tuto()
    kengi.get_game_ctrl().turn_on().loop()
    kengi.quit()
    print('bye!')
