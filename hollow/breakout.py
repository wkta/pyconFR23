# squelette du classique d'arcade "Breakout"
import katagames_engine as kengi


kengi.bootstrap_e()
pygame = kengi.pygame
N_BRICKS = 7
BRICKS_DIM = (60, 24)
BRICKS_LOC = (25, 50)


class GameModel(kengi.Emitter):
    pass


class GameTicker(kengi.EvListener):

    def __init__(self, m, refgame):
        super().__init__()
        self.game = refgame

    def on_quit(self, ev):
        self.game.gameover = True

    def on_paint(self, ev):
        pass

    def on_update(self, ev):
        pass

    def on_keydown(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self.game.gameover = True

    def on_keyup(self, ev):
        pass


class Breakout(kengi.GameTpl):
    def __init__(self):
        super().__init__()
        self.model = None
        self.ticker = None

    def init_video(self):
        kengi.init(2, 'my breakout game')

    def enter(self, vms=None):
        super().enter(vms)
        self.ticker = GameTicker(None, self)
        self.ticker.turn_on()


b = Breakout()
b.loop()
