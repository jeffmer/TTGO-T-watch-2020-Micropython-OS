from tempos import g,tc,sched, TOUCH_DOWN, TOUCH_UP,BLACK
from graphics import RED
import machine
from micropython import const
from pngtile import PNG_Tile
import math
import json
from time import ticks_ms,ticks_diff

MAX = const(768) # 256 * 3


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

def get_home():
    loc = json.loads(open("location.json").read())
    xy = deg2num(loc["lat"],loc["long"],16)
    topleft = num2deg(xy[0],xy[1],16)
    botright = num2deg(xy[0]+1,xy[1]+1,16)
    return xy, (degtopx(topleft[1],botright[1],loc["long"]),degtopx(topleft[0],botright[0],loc["lat"]))
    
TILE,XY = get_home()

TILES = [None,None,None,None]

def get_tiles():
    global HOME,XY
    i = 0 if XY[0]>128 else 1
    j = 0 if XY[1]>128 else 1
    topx = TILE[0]-i
    topy = TILE[1]-j
    for j in range(2):
        for i in range(2):
            print(topx+i,topy+j)
            TILES[i+2*j] = PNG_Tile(topx+i,topy+j,256*i,256*j)
            
def drawmap(x,y): # xy in tile coord space 0..511,0..511
    now = ticks_ms()
    x = 272 if x+240>512 else x
    y = 272 if y+240>512 else y
    for i in range(4):
        TILES[i].draw_chunk(x,y,x+239,y+239)
    g.show()
    print("Draw Time(ms): ",ticks_diff(ticks_ms(),now))
    
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