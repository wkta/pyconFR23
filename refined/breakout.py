# prototype du classique d'arcade "Breakout" en 185 lignes de code tt compris
import katagames_engine as kengi


kengi.bootstrap_e()
pygame = kengi.pygame
N_BRICKS = 7
BRICKS_DIM = (60, 24)
BRICKS_LOC = (25, 50)


class GameModel(kengi.Emitter):
    BALLSIZE = 14

    def __init__(self):
        super().__init__()
        scr_dim = kengi.get_surface().get_size()
        self.scr_w = scr_dim[0]
        ref_pos = [scr_dim[0]//2, scr_dim[1]]

        pl_width = 105
        self.player = pygame.Rect((ref_pos[0], ref_pos[1]-15), (pl_width, 8))
        self.player.left -= pl_width//2

        self.__ball_pos = [None, None]
        self.ball_rect = None
        setattr(self, 'ball_position', (ref_pos[0], ref_pos[1]-40))

        self.ball_v = pygame.math.Vector2()

        ox = BRICKS_DIM[0]+3
        self.bricks = [
            pygame.Rect(BRICKS_LOC[0]+ox*i, BRICKS_LOC[1], BRICKS_DIM[0], BRICKS_DIM[1]) for i in range(N_BRICKS)
        ]

        self.ignore_collision = 0

    def launch_ball(self):
        self.ball_v[0] = 68
        self.ball_v[1] = -113.3

    def update(self, dt):
        if self.ball_v.length() == 0:
            return
        IGNVAL = 8

        tmp = list(self.ball_position)
        tmp[0] += self.ball_v[0]*dt
        tmp[1] += self.ball_v[1]*dt

        # manage collisions
        rem = list()
        for br in self.bricks:
            if br.colliderect(self.ball_rect):
                rem.append(br)
        pl_hits = self.player.colliderect(self.ball_rect)

        if self.ignore_collision == 0:
            if len(rem) or pl_hits:
                self.ball_v[1] *= -1
                self.ignore_collision = IGNVAL  # dont check out of bounds
                for r in rem:
                    self.bricks.remove(r)

        self.ball_position = tmp

        # manage scr bounds
        if self.ignore_collision == 0:
            if (self.ball_rect.right >= self.scr_w) or self.ball_rect.left < 0:
                self.ball_v[0] *= -1
                self.ignore_collision = IGNVAL  # dont check out of bounds
            if self.ball_rect.top < 0:
                self.ball_v[1] *= -1
                self.ignore_collision = IGNVAL  # dont check out of bounds

        if self.ignore_collision > 0:
            self.ignore_collision -= 1

    @property
    def ball_position(self):
        return self.__ball_pos

    @ball_position.setter
    def ball_position(self, newp):
        self.__ball_pos[0], self.__ball_pos[1] = newp
        self.ball_rect = pygame.Rect(newp[0]-self.BALLSIZE, newp[1]-self.BALLSIZE, 2*self.BALLSIZE, 2*self.BALLSIZE)


class GameTicker(kengi.EvListener):
    BALL_COLOR = kengi.pal.japan['skyblue']
    PL_COLOR = kengi.pal.punk['flashypink']

    def __init__(self, m, refgame):
        super().__init__()
        self.mod = m
        self.game = refgame
        self.bcolors = dict()
        omega_col = list(kengi.pal.punk.listing)
        omega_col.reverse()
        omega_col = omega_col[7:]

        for k, br in enumerate(self.mod.bricks):
            self.bcolors[br.topleft] = omega_col[k]

        self.press_left = False
        self.press_right = False
        self.t_last_update = None

    def on_quit(self, ev):
        self.game.gameover = True

    def on_paint(self, ev):
        ev.screen.fill(kengi.pal.japan['navy'])
        for k, br in enumerate(self.mod.bricks):
            pygame.draw.rect(ev.screen, self.bcolors[br.topleft], br)
        pygame.draw.circle(
            ev.screen,
            self.BALL_COLOR,
            self.mod.ball_position,
            GameModel.BALLSIZE
        )
        pygame.draw.rect(  # -- debug
            ev.screen,
            'red',
            self.mod.ball_rect,
            1
        )
        pygame.draw.rect(ev.screen, self.PL_COLOR, self.mod.player)

    def on_update(self, ev):
        if self.press_left:
            self.mod.player.left -= 5
        elif self.press_right:
            self.mod.player.left += 5
        if self.t_last_update is None:
            pass
        else:
            dt = ev.curr_t - self.t_last_update
            self.mod.update(dt)

        self.t_last_update = ev.curr_t

    def on_keydown(self, ev):
        if ev.key == pygame.K_LEFT:
            self.press_left = True
        elif ev.key == pygame.K_RIGHT:
            self.press_right = True
        elif ev.key == pygame.K_SPACE:
            self.mod.launch_ball()
        elif ev.key == pygame.K_ESCAPE:
            self.game.gameover=True

    def on_keyup(self, ev):
        pkeys = pygame.key.get_pressed()
        if not pkeys[pygame.K_LEFT]:
            self.press_left = False
        if not pkeys[pygame.K_RIGHT]:
            self.press_right = False


class Breakout(kengi.GameTpl):
    def __init__(self):
        super().__init__()
        self.model = None
        self.ticker = None

    def init_video(self):
        kengi.init(2, 'my breakout game')

    def enter(self, vms=None):
        super().enter(vms)
        self.model = GameModel()

        self.ticker = GameTicker(self.model, self)
        self.ticker.turn_on()


b = Breakout()
b.loop()
