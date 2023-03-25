from tempos import g,tc,pm,sched, TOUCH_DOWN, TOUCH_UP,BLACK,WHITE
from fonts import roboto36
from graphics import RED,CYAN
import machine
from micropython import const
from pngtile import PNG_Tile
import math
import array
import json
from time import ticks_ms,ticks_diff

def disp_level(ll):
    global g
    g.setfont(roboto36)
    g.setfontalign(-1,-1)
    g.text(str(ll),180,10,WHITE)
    g.show()

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile, zoom)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

ZOOM = 12

def get_px(tile,loc):
    degtopx = lambda left,right,pos:int(256*(pos-left)/(right-left))
    topleft = num2deg(tile[0],tile[1],ZOOM)
    botright = num2deg(tile[0]+1,tile[1]+1,ZOOM)
    return degtopx(topleft[1],botright[1],loc[1]),degtopx(topleft[0],botright[0],loc[0])

home = json.loads(open("location.json").read())
LOCATION = (home["lat"],home["long"])
TILE = deg2num(LOCATION[0],LOCATION[1],ZOOM)
PX  =  get_px(TILE,LOCATION)
TILES    = [None,None,None,None]

def get_location():
    return LOCATION,ZOOM

def pixels_to_loc(x,y):
    global ZOOM
    pxtodeg = lambda left,right,px : left + px*(right-left)/256
    tilex = TILES[0]._tile[0]
    tiley = TILES[0]._tile[1]
    origin = num2deg(tilex,tiley,ZOOM)
    botright = num2deg(tilex+1,tiley+1,ZOOM)
    return pxtodeg(origin[0],botright[0],y), pxtodeg(origin[1],botright[1],x)
    
def create_tile(tx,ty,x,y):
    global ZOOM
    global TILES
    for i in range(4):
        tile = TILES[i]
        if not tile is None and not tile._data is None:
            if tile._tile[0] == tx and tile._tile[1] == ty:
                tile._stx =x
                tile._sty =y
                return tile
    #print(tx,ty)
    return PNG_Tile(tx,ty,ZOOM,x,y)

def  refresh_tiles():
        for i in range(4):
           tile = TILES[i]
           if not tile is None and tile._data is None:
               tile._decode()
               
def get_tiles():
    global TILE,PX,TILES
    saved = machine.freq()
    machine.freq(240000000)
    # quadrant for TILE
    i = 0 if PX[0]>128 else 1
    j = 0 if PX[1]>128 else 1
    topx = TILE[0]-i
    topy = TILE[1]-j
    PX = (i*256+PX[0], j*256+PX[1])
    temp = [None,None,None,None]
    for j in range(2):
        for i in range(2):
            temp[i+2*j] = create_tile(topx+i,topy+j,256*i,256*j)
    TILES = temp
    machine.freq(saved)
    
get_tiles()

class Marker:
    def __init__(self,loc,col):
        self._loc = loc
        self._col = col

    def draw(self,tx,ty):
        global ZOOM
        tile = deg2num(self._loc[0],self._loc[1],ZOOM)
        for j in range(2):
            for i in range(2):
                t = TILES[i+j*2]
                if t._tile == tile:
                    px = get_px(tile,self._loc)
                    x = px[0]+i*256-tx
                    y = px[1]+j*256-ty
                    if (x>5 and x<234 and y>3 and x<236):
                        g.ellipse(x,y,5,5,self._col,True)
                    return

markers = []
markers.append(Marker(LOCATION,CYAN))
markers.append(Marker((48.69322,-4.13183),RED))
markers.append(Marker((38.95074,20.76715),RED))

direction = array.array("h",[315,0,45,270,-1,90,225,180,135])
def drawArrow(dx,dy):
    a = direction[4+dx+dy*3]
    if a>=0:
        Arrow = array.array("h",[0,-30,10,30,-10,30])
        g.poly(120,120,Arrow,WHITE,True,a*math.pi/180)
    g.show()

def drawmap(cx,cy): # draw xy as centre of screen in tile coord space 0..511,0..511
    # return clipped top left corner
    def clip(v):
        v -=120
        v = v if v>0 else 0
        return v if v+240<=512 else 272
    
    x = clip(cx)
    y = clip(cy)
    for i in range(4):
        TILES[i].draw_chunk(x,y,x+239,y+239)
    for m in markers:
        m.draw(x,y)
    g.show()
    
def ontouch(tch):
    global x,y,PX,TILE,LOCATION,ZOOM
    dr = lambda v:-1 if v<60 else +1 if v>180 else 0
    outside = lambda v: v<0 or v>=512
    z = ZOOM
    if tch[2] == TOUCH_DOWN:
        x = tch[0]; y = tch[1]
    elif tch[2] == TOUCH_UP:
        dx = dr(x); dy = dr(y)
        newx = PX[0]+60*dx
        newy = PX[1]+60*dy
        if (dx==0 and dy==0): #zoom
                if x>120:
                    z+=2; z = 16 if z>16 else z
                else:
                    z-=2; z = 2 if z<2 else z
                disp_level(z)
        else:
            drawArrow(dx,dy)
        if outside(newx) or outside(newy) or not ZOOM == z:
            LOCATION = pixels_to_loc(newx,newy)
            ZOOM=z
            TILE = deg2num(LOCATION[0],LOCATION[1],ZOOM)
            PX = get_px(TILE,LOCATION)
            get_tiles()
        else:
            PX = (newx,newy)
        drawmap(PX[0],PX[1])

def safecall(tch):
    sched.setTimeout(10,ontouch,tch) 

listener = None

def app_init():
    global listener
    refresh_tiles()
    drawmap(PX[0],PX[1])
    listener = tc.addListener(safecall)
    
def app_end():
    global listener
    if not listener is None:
        tc.removeListener(listener)
    g.fill(BLACK)