from tempos import g, tc, sched, TOUCH_DOWN, TOUCH_UP, buzzer
from graphics import BLUE, GREEN, WHITE, BLACK
from fonts import roboto24
import array


class Theme:
    def __init__(self, fg, bg, pcol, border, font):
        self._fg = fg
        self._bg = bg
        self._pcol = pcol  # color when pressed
        self._bd = border
        self._font = font


class Button:
    def __init__(self, str, x, y, w, h, font=None, theme=None):
        self.str = str
        self._theme = (
            Theme(WHITE, BLUE, GREEN, WHITE, roboto24) if theme is None else theme
        )
        if not font is None:
            self._theme._font = font
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cb = None
        self.args = None
        self.pressed = False

    def callback(self, cb, *args):
        self.cb = cb
        self.args = args

    def draw(self, now=True):
        c = self._theme._bg if not self.pressed else self._theme._pcol
        g.setfont(self._theme._font)
        g.fill_rect(self.x, self.y, self.w, self.h, c)
        if c != self._theme._bd:
            g.rect(self.x, self.y, self.w, self.h, self._theme._bd)
        g.setfontalign(0, 0)
        g.text(self.str, self.x + self.w // 2, self.y + self.h // 2, self._theme._fg)
        g.setcolor(WHITE, BLACK)
        if now:
            g.show()

    def press(self):
        self.pressed = True
        self.draw()
        buzzer.click()

    def clear(self):
        self.pressed = False

    def release(self):
        self.pressed = False
        self.draw()
        if not self.cb is None:
            self.cb(*self.args)

    def istouched(self, x, y):
        return x > self.x and x < self.x + self.w and y > self.y and y < self.y + self.h


class RoundButton(Button):
    def draw(self, now=True):
        c = self._theme._bg if not self.pressed else self._theme._pcol
        g.setfont(self._theme._font)
        cx = self.x + self.w // 2
        cy = self.y + self.h // 2
        g.ellipse(cx, cy, self.w // 2, self.h // 2, c, True)
        if c != self._theme._bd:
            g.ellipse(cx, cy, self.w // 2, self.h // 2, self._theme._bd, False)
        g.setfontalign(0, 0)
        g.text(self.str, cx, cy, self._theme._fg)
        g.setcolor(WHITE, BLACK)
        if now:
            g.show()


class ArrowButton(Button):
    def __init__(self, str, x, y, w, h, font=None, theme=None, dir=0):
        self._arrow = self._getarrow(x, y, w, h, dir)
        super().__init__(str, x, y, w, h, font, theme)

    def _getarrow(self, x, y, w, h, dir):
        x1 = x + w - 1
        y1 = y + h - 1
        xmid = x + w // 2 - 1
        ymid = y + h // 2 - 1
        if dir == 0:  # north
            return array.array("h", [x, y1, xmid, y, x1, y1])
        elif dir == 1:  # east
            return array.array("h", [x, y1, x, y, x1, ymid])
        elif dir == 2:
            return array.array("h", [x, y, x1, y, xmid, y1])
        elif dir == 3:  # west
            return array.array("h", [x, ymid, x1, y, x1, y1])

    def draw(self, now=True):
        c = self._theme._bg if not self.pressed else self._theme._pcol
        g.setfont(self._theme._font)
        g.poly(0, 0, self._arrow, c, True)
        if c != self._theme._bd:
            g.poly(0, 0, self._arrow, self._theme._bd, False)
        if self.str != "":
            g.setfontalign(0, 0)
            g.text(
                self.str, self.x + self.w // 2, self.y + self.h // 2, self._theme._fg
            )
        g.setcolor(WHITE, BLACK)
        if now:
            g.show()


class ButtonMan:
    def __init__(self):
        self.buttons = []
        self.pressed = None
        self.listener = None
        self.clicker = buzzer.click

    def start(self):
        self.drawAll()
        self.listener = tc.addListener(self._safecall)

    def stop(self):
        if not self.listener is None:
            tc.removeListener(self.listener)

    def add(self, b):
        self.buttons.append(b)

    def drawAll(self):
        for b in self.buttons:
            b.draw(now=False)
        g.show()

    def _ontouch(self, tch):
        if tch[2] == TOUCH_DOWN:
            # print("touch",tch[0],tch[1])
            for b in self.buttons:
                if b.istouched(tch[0], tch[1]):
                    self.pressed = b
                    b.press()
                    self.clicker()
        elif not self.pressed is None:
            if tch[2] == TOUCH_UP:
                self.pressed.release()
                self.pressed = None
            else:
                self.pressed.clear()

    def _safecall(self, tch):
        sched.setTimeout(10, self._ontouch, tch)
