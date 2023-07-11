from micropython import const
from tempos import g, rtc, sched
from graphics import rgb, WHITE, BLACK, BLUE, CYAN, RED
from fonts import roboto24
import array
import math
import png
from time import ticks_ms, ticks_diff


def drawRotRect(w, r1, r2, angle, c):
    w2, ll, a = w // 2, r2 - r1, (angle + 270) * (math.pi / 180)
    coord = array.array("h", [0, -w2, ll, -w2, ll, w2, 0, w2])
    x, y = math.ceil(g.width // 2 + r1 * math.cos(a)), math.ceil(
        g.height // 2 + r1 * math.sin(a)
    )
    g.poly(x, y, coord, c, True, a)


W = const(240)
H = const(240)
R = const(120)
CX = const(120)
CY = const(120)
GREY = rgb(220, 220, 220)
months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

dialpic = png.getPNG("images/dial.png", WHITE)


def dial(t):
    g.fill(WHITE)
    png.drawPNG(dialpic, 0, 0)
    ds = "{:02}.{:s}".format(t[2], months[t[1] - 1])
    g.setfont(roboto24)
    g.setfontalign(0, -1)
    g.setcolor(BLACK, WHITE)
    g.text(ds, CX, 70)


def secH(a, c):
    drawRotRect(2, 3, R - 25, a, c)


def minH(a, c):
    drawRotRect(6, -20, R - 25, a, c)


def hourH(a, c):
    drawRotRect(8, -20, R - 50, a, c)


def onSecond():
    SD = rtc.datetime()
    # begin = ticks_ms()
    dial(SD)
    hourH(SD[4] * 30 + SD[5] // 2, BLACK)
    minH(SD[5] * 6, BLACK)
    g.ellipse(CX, CY, 6, 6, BLACK, True)
    secH(SD[6] * 6, RED)
    g.ellipse(CX, CY, 3, 3, RED, True)
    g.show()
    # print("onSecond = ", ticks_diff(ticks_ms(),begin))


ticker = None


def app_init():
    global SD, ticker
    SD = rtc.datetime()
    onSecond()
    ticker = sched.setInterval(1000, onSecond)


def app_end():
    sched.clearInterval(ticker)
    g.setcolor(WHITE, BLACK)
    g.fill(BLACK)
