from micropython import const
from tempos import g, pm, sched, settings
from graphics import rgb, WHITE, BLACK, YELLOW, GREY, GREEN, LIGHTGREY
from fonts import roboto24, roboto36
from button import ArrowButton, ButtonMan, Theme, Button
import math


class Label:
    def __init__(self, x, y, w, h, font, c):
        self.font = font
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.c = c

    def update(self, str, now=True):
        g.setfont(self.font)
        g.fill_rect(self.x, self.y, self.w, self.h, BLACK)
        g.setfontalign(0, 0)
        g.text(str, self.x + self.w // 2, self.y + self.h // 2, self.c)
        if now:
            g.show()


_X = const(50)
_Y = const(45)
_W = const(140)
_H = const(40)
_B = const(2)


class ValueDisplay:
    theme = Theme(WHITE, LIGHTGREY, GREEN, LIGHTGREY, roboto24)

    def __init__(self, title, Y, barorval, incr, userfn, buttonman):
        self._title = title
        self._YOFF = Y
        self._barorval = barorval
        self._incr = incr
        self._userfn = userfn
        self._minus = ArrowButton(
            "-", 0, self._YOFF + _Y, 50, _H, theme=self.theme, dir=3
        )
        self._plus = ArrowButton(
            "+", _X + _W, self._YOFF + _Y, 50, _H, theme=self.theme, dir=1
        )
        self._minus.callback(self.adjust, -self._incr)
        self._plus.callback(self.adjust, self._incr)
        buttonman.add(self._minus)
        buttonman.add(self._plus)

    def drawBar(self, v, now=True):
        g.fill_rect(_X, self._YOFF + _Y, _W, _H, LIGHTGREY)
        g.fill_rect(_X + _B, self._YOFF + _Y + _B, _W - 2 * _B, _H - 2 * _B, GREY)
        g.fill_rect(
            _X + _B + 2,
            self._YOFF + _Y + _B + 2,
            math.ceil((_W - 2 * _B - 4) * v),
            _H - _B * 2 - 4,
            YELLOW,
        )
        if now:
            g.show()

    def drawVal(self, v, now=True):
        g.setfont(roboto36)
        s = "{}".format(v)
        g.fill_rect(_X, self._YOFF + _Y, _W, _H, LIGHTGREY)
        g.fill_rect(_X + _B, self._YOFF + _Y + _B, _W - 2 * _B, _H - 2 * _B, GREY)
        g.setfontalign(0, -1)
        g.text(s, 120, self._YOFF + _Y + 3, WHITE)
        if now:
            g.show()

    def drawInit(self, v):
        g.setfont(roboto36)
        g.setfontalign(0, -1)
        g.text(self._title, 120, self._YOFF, WHITE)
        if self._barorval:
            self.drawBar(v, False)
        else:
            self.drawVal(v, False)

    def adjust(self, incr):
        v = self._userfn(incr)
        if self._barorval:
            self.drawBar(v)
        else:
            self.drawVal(v)


class SwitchPanel(Button):
    theme = Theme(WHITE, LIGHTGREY, GREEN, GREY, roboto24)
    _HT = 43

    def __init__(self, str, y, initState, onchange, buttonman):
        self._state = initState
        self._str = str
        self._Y = y
        self._change = onchange
        super().__init__(str, g.width - 60, y, 60, self._HT, None, self.theme)
        buttonman.add(self)

    def _drawroundrect(self, x, y, w, h, col):
        r = h // 2
        cx = x + r
        cy = y + r
        rw = w - 2 * r
        g.ellipse(cx, cy, r, r, col, True, 0x06)
        g.fill_rect(x + r, y, rw, h, col)
        g.ellipse(cx + rw, cy, r, r, col, True, 0x09)

    def _drawswitch(self, x, y, w, h, state):
        r = h // 2
        col = self.theme._pcol if state else self.theme._bd
        self._drawroundrect(x, y, w, h, col)
        g.ellipse(
            x + w - r if state else x + r, y + r, r - 2, r - 2, self.theme._bg, True
        )

    def draw(self, now=True):
        if not now:  # draw background
            self._drawroundrect(0, self._Y, g.width - 1, self._HT, LIGHTGREY)
            g.setfont(self.theme._font)
            y = self._Y + self._HT // 2
            g.setfontalign(-1, 0)
            g.text(self._str, self._HT // 2, y, self.theme._fg)
        self._drawswitch(g.width - 60, self._Y + 6, 54, 31, self._state)
        if now:
            g.show()

    def release(self):
        self.pressed = False
        self._state = not self._state
        self.draw()
        if not self._change is None:
            self._change(self._state)
