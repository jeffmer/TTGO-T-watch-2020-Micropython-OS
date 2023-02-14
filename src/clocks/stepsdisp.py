from micropython import const
from tempos import g,rtc,ac,sched
from graphics import rgb,WHITE,BLACK,BLUE,GREEN,RED,CYAN
from fonts import roboto18,bignumfont,roboto36
import array
import math
import png

W = const(240)
H = const(240)
R = const(120)
CX = const(120)
CY = const(120)
TARGET = 10000
GREY = rgb(200,200,200)
walkimage = png.getPNG('images/walking.png',BLACK)

def drawRotRect(w,r1,r2,angle,c):
    w2,ll,a = w//2,r2-r1,(angle+270)*(math.pi/180)
    coord = array.array("h",[0,-w2,ll,-w2,ll,w2,0,w2])
    x,y = math.ceil(g.width//2+r1*math.cos(a)),math.ceil(g.height//2+r1*math.sin(a))
    g.poly(x,y,coord,c,True,a)

def background():
    g.fill(BLACK)
    g.setfont(roboto18)
    c = GREY if ac.totalSteps()<TARGET else GREEN
    g.ellipse(CX,CY,R,R,c,True)
    g.ellipse(CX,CY,R-10,R-10,BLACK,True)
    g.fill_rect(0,H-36,W,36,BLACK)
    g.text("0",35,H-32,WHITE)
    g.setfontalign(1,-1)
    g.text(str(TARGET),W-5,H-32,WHITE)
    g.setcolor(BLACK,CYAN)
    png.drawPNG(walkimage,CX-walkimage[0]//2,H-walkimage[1])
    g.setcolor(WHITE,BLACK)

lastd = 0

def drawSteps():
    global lastd
    t = rtc.datetime()
    ds = '{:02}:{:02}'.format(t[4],t[5])
    g.setfont(roboto36)
    g.setfontalign(-1,-1)
    len_ds,_ = g.text_dim(ds)
    g.fill_rect(CX-len_ds//2-5,50,len_ds+10,40,BLACK)
    g.text(ds,CX-len_ds//2,50,WHITE)    
    steps = ac.totalSteps()
    g.setfont(bignumfont)
    st = "{}".format(steps)
    ll,hh = g.text_dim(st)
    g.fill_rect(CX-ll//2-1,CY-hh//2-1,ll+2,hh+2,BLACK);
    g.text(st,CX-ll//2,CY-hh//2,WHITE)
    c = GREEN
    if steps>TARGET :
        steps-=TARGET
        c = RED
    d = math.ceil(270*steps/TARGET)
    for a in range(lastd,d):
        drawRotRect(4,110,119,a+225,c);
    lastd=d
    g.show()

ticker = None

def app_init():
    global ticker,lastd
    background()
    lastd=0
    drawSteps()
    ticker = sched.setInterval(2000,drawSteps)

def app_end():
    sched.clearInterval(ticker)
    g.fill(BLACK)





