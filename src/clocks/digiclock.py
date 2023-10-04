from tempos import g, rtc, sched
from graphics import WHITE, BLACK, CYAN, LIGHTGREY
from fonts import hugefont

XOFF = 0 if g.width<=240 else 40

def drawtime():
    t = rtc.datetime()
    g.fill(BLACK)
    g.setfont(hugefont)
    g.setfontalign(-1, -1)
    g.text("{:02}".format(t[4]), XOFF, 45, WHITE)
    g.text("{:02}".format(t[5]), XOFF+125, 45, CYAN)
    g.text("{:02}".format(t[6]), XOFF+125, 130, LIGHTGREY)
    g.show()


def app_init():
    global clock
    drawtime()
    clock = sched.setInterval(1000, drawtime)


def app_end():
    global clock
    sched.clearInterval(clock)
    g.fill(BLACK)
