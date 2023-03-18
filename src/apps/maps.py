from tempos import g,tc,sched, TOUCH_DOWN, TOUCH_UP,BLACK
import machine
from micropython import const

MAX = const(1280) 
map = open("/sd/maps/ham.raw",'rb')

XPOS = 600
YPOS = 600

def drawmap(xoff,yoff):
    global map
    xoff =  MAX-240 if (xoff+240)>=MAX else xoff
    yoff =  MAX-240 if (yoff+240)>=MAX else yoff
    saved = machine.freq()
    machine.freq(240000000)
    bufaddr = memoryview(g._buf)
    for y in range(240):
       map.seek(xoff*2+(y+yoff)*2560)
       map.readinto(bufaddr[y*480:(y+1)*480],480)
    g.updateMod(0,0,239,239)
    g.show()
    machine.freq(saved)


def ontouch(tch):
    global x,y,XPOS,YPOS
    if tch[2] == TOUCH_DOWN:
        x = tch[0]; y = tch[1]
    elif tch[2] == TOUCH_UP:
        XPOS = XPOS-120 if x<60 else XPOS+120 if x>180 else XPOS
        YPOS = YPOS-120 if y<60 else YPOS+120 if y>180 else YPOS
        XPOS = MAX-240 if (XPOS+240)>=MAX else 0 if XPOS<0 else XPOS
        YPOS = MAX-240 if (YPOS+240)>=MAX else 0 if YPOS<0 else YPOS
        drawmap(XPOS,YPOS)

def safecall(tch):
    sched.setTimeout(10,ontouch,tch) 

listener = None

def app_init():
    global listener
    drawmap(XPOS,YPOS)
    listener = tc.addListener(safecall)

def app_end():
    global listener
    if not listener is None:
        tc.removeListener(listener)
    g.fill(BLACK)