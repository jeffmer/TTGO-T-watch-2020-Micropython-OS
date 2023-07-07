from micropython import const
from tempos import g, pm, sched
from graphics import rgb, WHITE, BLACK, GREEN
from fonts import roboto24, roboto36
import math

X = const(80)
Y = const(70)

batpercent = 50


def drawBat():
    g.fill(BLACK)
    global batpercent
    v = pm.batPercent()
    batpercent = v if v > 0 else batpercent
    g.setfont(roboto36)
    g.setfontalign(0, -1)
    g.text("Battery", 120, 20, WHITE)
    g.fill_rect(X, Y, 80, 32, WHITE)
    g.fill_rect(X + 4, Y + 4, 72, 24, BLACK)
    g.fill_rect(X + 6, Y + 6, math.ceil(68 * batpercent / 100), 20, GREEN)
    g.fill_rect(X + 80, Y + 8, 4, 16, WHITE)
    g.setfont(roboto24)
    g.setfontalign(-1, -1)
    g.text("{:02}%".format(batpercent), X, Y + 42)
    g.text("{:.1f}ma".format(-pm.batA()), X, Y + 72)
    g.text("{:.2f}V".format(pm.batV()), X, Y + 102)
    g.show()


ticker = None


def app_init():
    global ticker
    drawBat()
    ticker = sched.setInterval(1000, drawBat)


def app_end():
    sched.clearInterval(ticker)
    g.fill(BLACK)
