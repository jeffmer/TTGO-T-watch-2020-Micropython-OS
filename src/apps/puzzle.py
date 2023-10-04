from tempos import g, tc, sched, SWIPE_RIGHT, SWIPE_LEFT, SWIPE_DOWN, SWIPE_UP
from graphics import LIGHTGREY, WHITE, BLACK, RED
import loader
from button import Button, ButtonMan
from micropython import const
from fonts import roboto18, roboto24, hugefont
from random import randint

TILESIZE = const(50)
NSIDE = const(4)
TILES = const(16)
TOPX = 20 if g.width<=240 else 60
TOPY = const(0)


def shuffle(ll):
    for i in range(len(ll) - 1, 0, -1):
        j = randint(0, i + 1)
        ll[i], ll[j] = ll[j], ll[i]


def coord(pos):
    ix = pos % NSIDE
    iy = pos // NSIDE
    return TOPX + ix * TILESIZE, TOPY + iy * TILESIZE


def nextpos(pos, mv):
    ix = pos % NSIDE
    iy = pos // NSIDE
    if mv == SWIPE_DOWN:
        iy -= 1
    elif mv == SWIPE_UP:
        iy += 1
    elif mv == SWIPE_RIGHT:
        ix -= 1
    elif mv == SWIPE_LEFT:
        ix += 1
    else:
        return -1
    if ix < 0 or ix >= NSIDE or iy < 0 or iy >= NSIDE:
        return -1
    return iy * NSIDE + ix


def color(idt):
    if idt == 0:
        return WHITE, WHITE
    ix = (idt - 1) % NSIDE
    iy = (idt - 1) // NSIDE
    if iy % 2 == 0:
        black = ix % 2 == 1
    else:
        black = ix % 2 == 0
    return BLACK if black else WHITE, WHITE if black else BLACK


def even(v):
    return v % 2 == 0


class Tile:
    def __init__(self, ident):
        self._id = ident
        self._fg, self._bg = color(ident)

    def ident(self):
        return self._id

    def draw(self, x, y):
        g.fill_rect(x, y, TILESIZE, TILESIZE, self._bg)
        if self._id == 0:  # blank space has id 0
            return
        g.rect(x, y, TILESIZE, TILESIZE, self._fg)
        g.setfont(roboto24)
        g.setfontalign(0, 0)
        g.setcolor(self._fg, self._bg)
        g.text(str(self._id), x + TILESIZE // 2, y + TILESIZE // 2)
        g.setcolor(WHITE, BLACK)


class Board:
    def __init__(self):
        self._tiles = []
        for i in range(1, TILES):
            self._tiles.append(Tile(i))
        self._gaptile = Tile(0)
        self._tiles.append(self._gaptile)
        self._gpos = 15
        self._moves = 0

    def inversions(self):
        invs = 0
        for i in range(0, TILES):
            ida = self._tiles[i].ident()
            for j in range(i + 1, TILES):
                idb = self._tiles[j].ident()
                if idb > 0 and ida > idb:
                    invs += 1
        return invs

    def ended(self):
        for i in range(1, TILES):
            if not self._tiles[i - 1].ident() == i:
                return False
        return True

    def is_solvable(self):
        invs = self.inversions()
        y = self.gap() // NSIDE
        return (even(y) and not even(invs)) or (not even(y) and even(invs))

    def newboard(self):
        self._moves = 0
        shuffle(self._tiles)
        self._gpos = self._tiles.index(self._gaptile)
        if not self.is_solvable():
            a = 0 if not self._gpos == 0 else 2
            b = 1 if not self._gpos == 1 else 2
            self._tiles[a], self._tiles[b] = self._tiles[b], self._tiles[a]
        self.drawall()

    def gap(self):
        return self._gpos

    def draw_score(self):
        g.setfont(hugefont)
        g.setfontalign(0, 0)
        g.text(str(self._moves), 120, 120, RED)

    def move(self, pos):
        src = self._tiles[pos]
        dst = self._tiles[self._gpos]
        src.draw(*coord(self._gpos))
        dst.draw(*coord(pos))
        self._tiles[pos] = dst
        self._tiles[self._gpos] = src
        self._gpos = pos
        self._moves += 1
        if self.ended():
            self.draw_score()
            g.show()
            return True
        else:
            g.show()
            return False

    def drawall(self):
        for i in range(0, TILES):
            self._tiles[i].draw(*coord(i))


bd = Board()


def onswipe(tch):
    tileno = nextpos(bd.gap(), tch[2])
    if tileno < 0:
        return
    if bd.move(tileno):
        actPause()


def safeswipe(tch):
    sched.setTimeout(10, onswipe, tch)


_ACTIVE = False
touch = None


def actPlay():
    global _ACTIVE, touch
    if not _ACTIVE:
        loader.setapplock(True)
        touch = tc.addListener(safeswipe)
        _ACTIVE = True
    if bd.ended():
        bd.newboard()
        g.show()


def actPause():
    global _ACTIVE, touch
    loader.setapplock(False)
    _ACTIVE = False
    if touch is not None:
        tc.removeListener(touch)
        touch = None


play = Button("Play", TOPX, 205, 60, 30, roboto18)
pause = Button("Pause", TOPX+140, 205, 60, 30, roboto18)
buttons = ButtonMan()
buttons.add(pause)
buttons.add(play)
play.callback(actPlay)
pause.callback(actPause)


def app_init():
    g.fill(BLACK)
    bd.drawall()
    if bd.ended():
        bd.draw_score()
    buttons.start()


def app_end():
    buttons.stop()
    actPause()  # can be called due to alarm
    g.fill(BLACK)
