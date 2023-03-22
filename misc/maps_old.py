from tempos import g,tc,sched, TOUCH_DOWN, TOUCH_UP,BLACK
from graphics import RED
import machine
from micropython import const
import math
import json

MAX = const(768) # 256 * 3
map = open("/sd/maps/map.raw",'rb')

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def degtopx(left,right,pos):
    return int(256*(pos-left)/(right-left))
def get_loc():
    loc = json.loads(open("location.json").read())
    xy = deg2num(loc["lat"],loc["long"],16)
    topleft = num2deg(xy[0],xy[1],16)
    botright = num2deg(xy[0]+1,xy[1]+1,16)
    return (256+degtopx(topleft[1],botright[1],loc["long"]),256+degtopx(topleft[0],botright[0],loc["lat"]))
    
HOME = get_loc()
XPOS = HOME[0]-120
YPOS = HOME[1]-120

def drawmap(xoff,yoff):
    global map
    xoff =  MAX-240 if (xoff+240)>=MAX else xoff
    yoff =  MAX-240 if (yoff+240)>=MAX else yoff
    saved = machine.freq()
    machine.freq(240000000)
    bufaddr = memoryview(g._buf)
    for y in range(240):
       map.seek(xoff*2+(y+yoff)*1536)
       map.readinto(bufaddr[y*480:(y+1)*480],480)
    g.updateMod(0,0,239,239)
    cx = HOME[0]-xoff
    cy = HOME[1]-yoff
    if (cx>0 and cx<240 and cy>0 and cy<240):
        g.ellipse(cx,cy,5,5,RED,True)
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