from micropython import const
from tempos import g, rtc, sched, sw, disable_sleep, enable_sleep
from drivers.switch import PRESSED, CLICK, LONG_PRESS, DOUBLE_CLICK
from wifi import connect, disconnect

from graphics import rgb, WHITE, BLACK, GREEN, LIGHTGREEN, RED, BLUE,MAGENTA, YELLOW
from widgets import Label
from fonts import glcdfont, roboto24, roboto18
import array
import math
from time import ticks_ms, ticks_diff
from opensky import getupdate,pxAirPos,degtopx,CallSign, Country, Long, Lat, Alt, Landed, Speed, Heading,planecolor
from config import AIRLONG, AIRLAT, AIRNAME
from adsbdb import getDetail
import machine

CR1 = const(115)
CR2 = const(70)
CR3 = const(35)
CX = const(120)
CY = const(120) 

def background():
    g.setcolor(BLACK)
    g.fill(BLACK)
    g.ellipse(CX, CY, CR1, CR1, GREEN, False)
    g.ellipse(CX, CY, CR2, CR2, LIGHTGREEN, False)
    g.ellipse(CX, CY, CR3, CR3, LIGHTGREEN, False)

POS =315
lastupdate =0

def sweep():
    global POS
    a = POS * (math.pi / 180)
    x = math.ceil(CX + CX * math.sin(a))
    y = math.ceil(CY - CY * math.cos(a))
    g.line(CX, CY, x, y, GREEN)
    POS =(POS+1) % 360
    

def drawAirport():
    x,y = degtopx(AIRLONG,AIRLAT)
    g.ellipse(x,y,4,4,MAGENTA,True)
    g.text(AIRNAME,x,y+14,MAGENTA)


def drawPlane(name,x, y, angle, c):
    g.poly(x, y, array.array("h", [0,-7, 5, 7, -5, 7]), c, True, angle)
    g.text(name,x,y+14,LIGHTGREEN)
    
    
def drawDetail(a):
    y = 80
    x = 120
    b,airline,fromloc,toloc = getDetail(a[CallSign])
    g.setcolor(BLACK)
    g.fill(BLACK)
    g.setfontalign(0,0)
    g.setfont(roboto24)
    g.text(a[CallSign],x,y,GREEN)
    g.setfont(glcdfont)
    y=y+24
    g.text("ALT {} m".format(int(a[Alt])),x,y,GREEN)
    y=y+18
    g.text("SPD {} mph".format(int(a[Speed] * 2.237)),x,y,GREEN)
    y=y+18
    g.text("HDG {} deg".format(int(a[Heading])),x,y,GREEN)
    y=y+18
    if b:
        g.text("Airline: {}".format(airline),x,y,GREEN)
        y=y+18
        g.text("From: {}".format(fromloc),x,y,GREEN)
        y=y+18
        g.text("To: {}".format(toloc),x,y,GREEN)    
    g.poly(x, 50, array.array("h", [0,-10, 7, 10, -7, 10]), planecolor(a[Alt]), True, math.radians(a[Heading]))
    g.show()

planes = None
lastupdate = 0
index = None
clicked = False

def mod(a):
    global planes
    if planes is None:
        return 0
    n = len(planes)
    return a - n if a >= n else a + n if a < 0 else a

def select(v):
    global planes,ticker,clicked
    global index
    if v == LONG_PRESS:
        if not clicked:
            clicked = True
            sched.clearInterval(ticker)
            if not planes is None:
                drawDetail(planes[index])
        else:
            clicked = False
            ticker = sched.setInterval(60, draw)
    elif v == CLICK:
        if (not planes is None ) and index is None:
            index = 0
        elif not index is None:
            index = mod(index+1)
    
def draw():
    global planes,POS,lastupdate
    g.setfont(glcdfont)
    g.setfontalign(0,0)
    background()
    drawAirport()
    now = ticks_ms()
    if POS==0:
        lastupdate = ticks_ms()
        planes=getupdate()
    dt = ticks_diff(now,lastupdate)/1000
    if planes:
        i=0
        for ac in planes:
            p = pxAirPos(ac,dt)
            drawPlane(p[0],p[1],p[2],p[3], WHITE if not index is None and index == i else p[4])
            i = i + 1
    sweep()
    g.show()

ticker = None
switch = None

status = Label(20, 200, 160, 40, roboto18, YELLOW)
progress = Label(200, 200, 40, 40, roboto18, YELLOW)

def app_init():
    global ticker,switch
    disable_sleep()
    machine.freq(240000000)
    connect(status,progress)
    switch = sw.addListener(select) 
    draw()
    ticker = sched.setInterval(60, draw)


def app_end():
    global ticker, switch
    sched.clearInterval(ticker)
    sw.removeListener(switch)
    disconnect()
    machine.freq(160000000)
    g.fill(BLACK)
    enable_sleep()