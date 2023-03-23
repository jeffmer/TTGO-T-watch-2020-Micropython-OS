from tempos import g,tc,sched, TOUCH_DOWN, TOUCH_UP,BLACK
from graphics import RED
import machine
from micropython import const
from pngtile import PNG_Tile
import math
import json
from time import ticks_ms,ticks_diff

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

def get_loc(loc):
    degtopx = lambda left,right,pos:int(256*(pos-left)/(right-left))
    tile = deg2num(loc[0],loc[1],16)
    topleft = num2deg(tile[0],tile[1],16)
    botright = num2deg(tile[0]+1,tile[1]+1,16)
    return tile, (degtopx(topleft[1],botright[1],loc[1]),degtopx(topleft[0],botright[0],loc[0]))

home = json.loads(open("location.json").read())
LOCATION = (home["lat"],home["long"])
TILE,PX  = get_loc(LOCATION)
TILES    = [None,None,None,None]

def get_location():
    return LOCATION

def pixels_to_loc(x,y):
    pxtodeg = lambda left,right,px : left + px*(right-left)/256
    tilex = TILES[0]._tile[0]
    tiley = TILES[0]._tile[1]
    origin = num2deg(tilex,tiley,16)
    botright = num2deg(tilex+1,tiley+1,16)
    return pxtodeg(origin[0],botright[0],y), pxtodeg(origin[1],botright[1],x)
    
def create_tile(tx,ty,x,y):
    global TILES
    for i in range(4):
        tile = TILES[i]
        if not tile is None and not tile._data is None:
            if tile._tile[0] == tx and tile._tile[1] == ty:
                tile._stx =x
                tile._sty =y
                return tile
    #print(tx,ty)
    return PNG_Tile(tx,ty,x,y)

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
    g.show()
    
def ontouch(tch):
    global x,y,PX,TILE,LOCATION
    dr = lambda v:-1 if v<60 else +1 if v>180 else 0
    outside = lambda v: v<0 or v>=512
    if tch[2] == TOUCH_DOWN:
        x = tch[0]; y = tch[1]
    elif tch[2] == TOUCH_UP:
        newx = PX[0]+120*dr(x)
        newy = PX[1]+120*dr(y)
        if outside(newx) or outside(newy):
            LOCATION = pixels_to_loc(newx,newy)
            TILE,PX = get_loc(LOCATION)
            get_tiles()
        else:
            PX = (newx,newy)
        drawmap(PX[0],PX[1])

def safecall(tch):
    sched.setTimeout(10,ontouch,tch) 

listener = None

def app_init():
    global listener
    get_tiles()
    drawmap(PX[0],PX[1])
    listener = tc.addListener(safecall)

def app_end():
    global listener
    if not listener is None:
        tc.removeListener(listener)
    g.fill(BLACK)