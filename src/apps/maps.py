from tempos import g, tc, pm, sched, TOUCH_DOWN, TOUCH_UP, BLACK, WHITE
from fonts import roboto36
from fonts import roboto24
from button import Theme, RoundButton, ButtonMan
from graphics import rgb, RED, CYAN, GREEN
import machine
from micropython import const
from pngtile import PNG_Tile
import math
import array
import json
from time import ticks_ms, ticks_diff


LIGHTGREY = rgb(200, 200, 200)
z_theme = Theme(WHITE, LIGHTGREY, GREEN, LIGHTGREY, roboto24)

ZOOM = 12
SHIFT = 40 if g.width>240 else 0

def disp_level(ll):
    global g
    g.setfont(roboto36)
    g.setfontalign(-1, -1)
    g.text(str(ll), 180+SHIFT, 10, WHITE)
    g.show()


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile, zoom)


def num2deg(xtile, ytile, zoom):
    n = 2.0**zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)





def get_px(tile, loc):
    def degtopx(left, right, pos):
        return int(256 * (pos - left) / (right - left))

    topleft = num2deg(tile[0], tile[1], ZOOM)
    botright = num2deg(tile[0] + 1, tile[1] + 1, ZOOM)
    return degtopx(topleft[1], botright[1], loc[1]), degtopx(
        topleft[0], botright[0], loc[0]
    )


home = json.loads(open("location.json").read())
LOCATION = (home["lat"], home["long"])
TILE = deg2num(LOCATION[0], LOCATION[1], ZOOM)
PX = get_px(TILE, LOCATION)
TILES = [None, None, None, None]


def get_location():
    return LOCATION, ZOOM


def pixels_to_loc(x, y):
    global ZOOM

    def pxtodeg(left, right, px):
        return left + px * (right - left) / 256

    tilex = TILES[0]._tile[0]
    tiley = TILES[0]._tile[1]
    origin = num2deg(tilex, tiley, ZOOM)
    botright = num2deg(tilex + 1, tiley + 1, ZOOM)
    return pxtodeg(origin[0], botright[0], y), pxtodeg(origin[1], botright[1], x)


def create_tile(tx, ty, x, y):
    global ZOOM
    global TILES
    for i in range(4):
        tile = TILES[i]
        if tile is not None and tile._data is not None:
            if tile._tile[0] == tx and tile._tile[1] == ty:
                tile._stx = x
                tile._sty = y
                return tile
    # print(tx,ty)
    return PNG_Tile(tx, ty, ZOOM, x, y)


def refresh_tiles():
    for i in range(4):
        tile = TILES[i]
        if tile is not None and tile._data is None:
            tile._decode()


def get_tiles():
    global TILE, PX, TILES
    saved = machine.freq()
    machine.freq(240000000)
    # quadrant for TILE
    i = 0 if PX[0] > 128 else 1
    j = 0 if PX[1] > 128 else 1
    topx = TILE[0] - i
    topy = TILE[1] - j
    PX = (i * 256 + PX[0], j * 256 + PX[1])
    temp = [None, None, None, None]
    for j in range(2):
        for i in range(2):
            temp[i + 2 * j] = create_tile(topx + i, topy + j, 256 * i, 256 * j)
    TILES = temp
    machine.freq(saved)


get_tiles()


class Marker:
    def __init__(self, loc, col):
        self._loc = loc
        self._col = col

    def update(self, loc):
        self._loc = loc

    def draw(self, tx, ty, doit=True):
        global ZOOM
        tile = deg2num(self._loc[0], self._loc[1], ZOOM)
        for j in range(2):
            for i in range(2):
                t = TILES[i + j * 2]
                if t._tile == tile:
                    px = get_px(tile, self._loc)
                    x = px[0] + i * 256 - tx
                    y = px[1] + j * 256 - ty
                    if x > 5 and x < 234 and y > 3 and x < 236:
                        if doit:
                            g.ellipse(x+SHIFT, y, 5, 5, self._col, True)
                        return True
                    else:
                        return False
        return False


homemark = Marker(LOCATION, CYAN)
markers = []
markers.append(homemark)
markers.append(Marker((48.69322, -4.13183), RED))
markers.append(Marker((38.95074, 20.76715), RED))

direction = array.array("h", [315, 0, 45, 270, -1, 90, 225, 180, 135])


def drawArrow(dx, dy):
    a = direction[4 + dx + dy * 3]
    if a >= 0:
        Arrow = array.array(
            "h", [0, -30, 15, -15, 5, -15, 5, 30, -5, 30, -5, -15, -15, -15]
        )
        g.poly(120+SHIFT, 120, Arrow, WHITE, True, a * math.pi / 180)
    g.show()


def drawmap(cx, cy):  # draw xy as centre of screen in tile coord space 0..511,0..511
    # return clipped top left corner
    def clip(v):
        v -= 120
        v = v if v > 0 else 0
        return v if v + 240 <= 512 else 272

    x = clip(cx)
    y = clip(cy)
    for i in range(4):
        TILES[i].draw_chunk(x, y, x + 239, y + 239)
    for m in markers:
        m.draw(x, y)
    g.show()


def ontouch(tch):
    global x, y, PX, TILE, LOCATION, ZOOM

    def dr(v):
        return -1 if v < 60 else +1 if v > 180 else 0

    def outside(v):
        return v - 120 < 0 or v + 120 >= 512

    if tch[2] == TOUCH_DOWN:
        x = tch[0]
        y = tch[1]
    elif tch[2] == TOUCH_UP:
        if x<60 or x>260:
            return
        dx = dr(x-SHIFT)
        dy = dr(y)
        newx = PX[0] + 60 * dx
        newy = PX[1] + 60 * dy
        if dx == 0 and dy == 0:  # zoom
            return
        drawArrow(dx, dy)
        if outside(newx) or outside(newy):  
            LOCATION = pixels_to_loc(newx, newy)
            TILE = deg2num(LOCATION[0], LOCATION[1], ZOOM)
            PX = get_px(TILE, LOCATION)
            get_tiles()
        else:
            PX = (newx, newy)
        drawmap(PX[0], PX[1])
        
def zoom(iv):
    global PX, TILE, LOCATION, ZOOM
    z = ZOOM+iv
    newz = z if z<=18 and z>=2 else ZOOM
    disp_level(newz)
    if newz != ZOOM:
        ZOOM=newz
        TILE = deg2num(LOCATION[0], LOCATION[1], ZOOM)
        PX = get_px(TILE, LOCATION)
        get_tiles()
        drawmap(PX[0], PX[1])
        
minusZ = RoundButton("-", 0, 100, 40, 40, theme=z_theme)
plusZ = RoundButton("+", 280, 100, 40, 40, theme=z_theme)
buttons = ButtonMan()
buttons.add(plusZ)
buttons.add(minusZ)
minusZ.callback(zoom,-2)
plusZ.callback(zoom,2)

def safecall(tch):
    sched.setTimeout(10, ontouch, tch)


def onGPS(p):
    global homemark, LOCATION, TILE, ZOOM, PX
    homemark.update(p)
    if not homemark.draw(PX[0], PX[1], False):
        LOCATION = p
        TILE = deg2num(LOCATION[0], LOCATION[1], ZOOM)
        PX = get_px(TILE, LOCATION)
        get_tiles()
    drawmap(PX[0], PX[1])


listener = None
gpslistener = None

def app_init():
    global listener, gpslistener
    refresh_tiles()
    drawmap(PX[0], PX[1])
    listener = tc.addListener(safecall)
    buttons.start()
#    gpslistener = gps.addListener(onGPS)


def app_end():
    global listener, gpslistener
    buttons.stop()
    if listener is not None:
        tc.removeListener(listener)
    if gpslistener is not None:
        gps.removeListener(gpslistener)
    g.fill(BLACK)
