import katagames_engine as kengi

kengi.bootstrap_e()


class MinimalistGame(kengi.GameTpl):

    def init_video(self):
        kengi.init()

    def update(self, infot):
        for ev in kengi.pygame.event.get():
            if ev.type == kengi.pygame.QUIT:
                self.gameover = True


b = MinimalistGame()
b.loop()
