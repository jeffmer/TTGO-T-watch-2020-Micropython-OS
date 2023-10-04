from micropython import const
from tempos import g, rtc, sched
from graphics import rgb, WHITE, BLACK, BLUE, CYAN, RED
from fonts import roboto18, roboto24
import array
import math
from time import ticks_ms, ticks_diff


def drawRotRect(w, r1, r2, angle, c):
    w2, ll, a = w // 2, r2 - r1, (angle + 270) * (math.pi / 180)
    coord = array.array("h", [0, -w2, ll, -w2, ll, w2, 0, w2])
    x, y = math.ceil(g.width // 2 + r1 * math.cos(a)), math.ceil(
        g.height // 2 + r1 * math.sin(a)
    )
    g.poly(x, y, coord, c, True, a)


W = g.width
H = const(240)
R = const(120)
CX = const(120)
CY = const(120)
GREY = rgb(220, 220, 220)


def dial():
    g.setcolor(WHITE)
    g.setfont(roboto24)
    g.setfontalign(0, 0)
    r = R - 10
    for i in range(1, 13):
        a = i * math.pi / 180
        x = CX + math.ceil(math.sin(a * 30) * r)
        y = CY - math.ceil(math.cos(a * 30) * r)
        if i == 12 or i == 11 or i == 1:
            y += 3
        s = str(i)
        g.text(s, x, y)


def secH(a, c):
    drawRotRect(2, 3, R - 30, a, c)


def minH(a, c):
    drawRotRect(4, 6, R - 32, a, c)


def hourH(a, c):
    drawRotRect(6, 6, R - 56, a, c)


def onSecond():
    SD = rtc.datetime()
    #   begin = ticks_ms()
    g.ellipse(CX, CY, R - 30, R - 30, BLACK, True)
    hourH(SD[4] * 30 + SD[5] // 2, WHITE)
    minH(SD[5] * 6, WHITE)
    g.ellipse(CX, CY, 6, 6, WHITE, True)
    secH(SD[6] * 6, RED)
    g.ellipse(CX, CY, 3, 3, RED, True)
    g.show()


#   print("onSecond = ", ticks_diff(ticks_ms(),begin))

ticker = None


def app_init():
    global SD, ticker
    SD = rtc.datetime()
    # draw bezel
    dial()
    onSecond()
    ticker = sched.setInterval(1000, onSecond)


def app_end():
    sched.clearInterval(ticker)
    g.fill(BLACK)
