from micropython import const
from tempos import g,rtc,sched
from graphics import rgb,WHITE,BLACK,BLUE,CYAN,RED
from fonts import roboto18
import array
import math
from time import ticks_ms,ticks_diff

def drawRotRect(w,r1,r2,angle,c):
    w2,ll,a = w//2,r2-r1,(angle+270)*(math.pi/180)
    coord = array.array("h",[0,-w2,ll,-w2,ll,w2,0,w2])
    x,y = math.ceil(g.width//2+r1*math.cos(a)),math.ceil(g.height//2+r1*math.sin(a))
    g.poly(x,y,coord,c,True,a)

W = const(240)
H = const(240)
R = const(120)
CX = const(120)
CY = const(120)
GREY = rgb(220,220,220)

def dial():
    begin = ticks_ms()
    for a in range(0,360,6):
        if a%30 != 30:
            theta = a*math.pi/180
            g.line(CX,CY,CX+int(170*math.sin(theta)),CY-int(170*math.cos(theta)),GREY)
    g.fill_rect(16,16,W-32,H-32,BLACK)
    for a in range(0,360,30):
        drawRotRect(2,R-100,170,a,WHITE)
    g.fill_rect(24,24,W-48,H-48,BLACK)
  
def calcnumpos():
    d,e = 95,10
    def s(a):
        return CX+math.floor(d*math.sin(a*30*math.pi/180))
    def c(a):
        return CY-math.floor(d*math.cos(a*30*math.pi/180))                  
    p = array.array("h",[i for i in range(0,24)])
    for i in range(0,12):
        p[2*i]=s(i); p[2*i+1]=c(i)
    p[1]=p[1]+e; p[23]=p[1]; p[3]=p[1]
    p[6]=p[6]-e; p[4]=p[6]; p[8]=p[6]
    p[13]=p[13]-e+2; p[11]=p[13]; p[15]=p[13]
    p[18]=p[18]+e; p[16]=p[18]; p[20]=p[18]
    return p

numpos = calcnumpos()
  
def numdial():
    g.setfont(roboto18)
    g.setfontalign(0,0)
    for a in range(0,12):
        s = "{:02}".format(60 if a==0 else a*5)
        g.text(s,numpos[a*2],numpos[a*2+1],GREY)

def secH(a,c):
    drawRotRect(2,3,R-30,a,c)

def minH(a,c):
    drawRotRect(4,6,R-32,a,c)

def hourH(a,c):
    drawRotRect(6,6,R-56,a,c)

def onSecond():
    SD = rtc.datetime()
#   begin = ticks_ms()
    g.fill_rect(24,24,W-48,H-48,BLACK)
    numdial()
    hourH(SD[4]*30+SD[5]//2,WHITE)
    minH(SD[5]*6,WHITE)
    g.ellipse(CX, CY, 6, 6, WHITE,True)
    secH(SD[6]*6,RED)
    g.ellipse(CX, CY, 3, 3, RED,True)
    g.show()
#   print("onSecond = ", ticks_diff(ticks_ms(),begin))

ticker = None

def app_init():
    global SD, ticker
    SD = rtc.datetime();
    # draw bezel
    dial(); numdial()
    onSecond();
    ticker = sched.setInterval(1000,onSecond)
    
def app_end():
    sched.clearInterval(ticker)
    g.fill(BLACK)




