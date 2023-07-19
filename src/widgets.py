import time
from micropython import const
from tempos import g, pm, sched, settings
from graphics import rgb, WHITE, BLACK, YELLOW, GREY, GREEN, LIGHTGREY, RED
from fonts import roboto18, roboto24, roboto36
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



class ValueDisplay:
    theme = Theme(WHITE, LIGHTGREY, GREEN, LIGHTGREY, roboto24)

    def __init__(self, title, Y, barorval, incr, userfn, buttonman, font=roboto36):
        self._title = title
        self._YOFF = Y
        self._barorval = barorval
        self._incr = incr
        self._userfn = userfn
        self._X = const(50)
        self._Y = const(35)
        self._W = const(140)
        self._H = const(40)
        self._B = const(2)
        self._minus = ArrowButton(
            "-", 0, self._YOFF + self._Y, 50, self._H, theme=self.theme, dir=3
        )
        self._plus = ArrowButton(
            "+", self._X + self._W, self._YOFF + self._Y, 50, self._H, theme=self.theme, dir=1
        )
        self._minus.callback(self.adjust, -self._incr)
        self._plus.callback(self.adjust, self._incr)
        buttonman.add(self._minus)
        buttonman.add(self._plus)
        self._font = font

    def drawBar(self, v, now=True):
        g.fill_rect(self._X, self._YOFF + self._Y, self._W, self._H, LIGHTGREY)
        g.fill_rect(self._X + self._B, self._YOFF + self._Y + self._B, self._W - 2 * self._B, self._H - 2 * self._B, GREY)
        g.fill_rect(
            self._X + self._B + 2,
            self._YOFF + self._Y + self._B + 2,
            math.ceil((self._W - 2 * self._B - 4) * v),
            self._H - self._B * 2 - 4,
            YELLOW,
        )
        if now:
            g.show()

    def drawVal(self, v, now=True):
        g.setfont(self._font)
        s = "{}".format(v)
        g.fill_rect(self._X, self._YOFF + self._Y, self._W, self._H, LIGHTGREY)
        g.fill_rect(self._X + self._B, self._YOFF + self._Y + self._B, self._W - 2 * self._B, self._H - 2 * self._B, GREY)
        g.setfontalign(0, -1)
        g.text(s, 120, self._YOFF + self._Y + 3, WHITE)
        if now:
            g.show()

    def drawInit(self, v):
        g.setfont(self._font)
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
        if self._change is not None:
            self._change(self._state)

class Clock:
    "clock appearing at the top of the screen"
    def __init__(self, enabled=True):
        self.on_screen = None
        self.enabled = enabled

    def draw(self):
        """Redraw the clock from scratch.

        The container is required to clear the canvas prior to the redraw
        and the clock is only drawn if it is enabled.
        """
        self.on_screen = None
        self.update()

    def update(self):
        """Update the clock widget if needed.

        This is a lazy update that only redraws if the time has changes
        since the last call *and* the clock is enabled.

        :returns: An time tuple if the time has changed since the last call,
                  None otherwise.
        """
        now = time.localtime()
        on_screen = self.on_screen

        if on_screen and on_screen == now:
            return None

        if self.enabled and (not on_screen
                or now[4] != on_screen[4] or now[3] != on_screen[3]):
            t1 = '{:02}:{:02}'.format(now[3], now[4])

            g.setfont(roboto18)
            g.setcolor(WHITE)
            g.text(t1, x=100, y=0)

        self.on_screen = now
        g.show()


class BatteryMeter:
    """Battery meter widget.

    A simple battery meter with a charging indicator, will draw at the
    top-right of the display.
    """
    def __init__(self):
        self.level = -2

    def draw(self):
        """Draw from meter (from scratch)."""
        self.level = -2
        self.update()

    def update(self):
        """Update the meter.

        The update is lazy and won't redraw unless the level has changed.
        """
        level = pm.batPercent()
        unit = settings.battery_unit

        if level == self.level:
            return

        g.setfont(roboto18)
        if pm.batA() > 0:  # is charging
            col = GREEN
        elif level <= 30:
            col = RED
        else:
            col = WHITE
        g.setcolor(col)
        if unit == "volt":
            val = "{}V".format(round(pm.batV(), 1))
        elif unit == "percent":
            val = "{}%".format(level)
        g.text(val, x=200, y=0)
        self.level = level
        g.show()


class StatusBar:
    """Combo widget to handle time and battery level."""
    def __init__(self):
        self._clock = Clock()
        self._meter = BatteryMeter()

    def draw(self):
        """Redraw the status bar from scratch."""
        self._clock.draw()
        self._meter.draw()

    def update(self):
        """Lazily update the status bar.
        """
        self._clock.update()
        self._meter.update()
