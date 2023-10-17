from tempos import g
from graphics import WHITE, BLACK, YELLOW
from fonts import roboto18, roboto24, roboto36
from button import Button, ButtonMan
import time
from widgets import Label
from wifi import do_connected_action
from urequests import request,post
from config import GOOGLE_KEY
import math
import json
import os
from apps.maps import get_location

status = Label(10, 80, 180, 40, roboto24, YELLOW)
progress = Label(200, 80, 40, 40, roboto24, YELLOW)

session = " "

maptype = '{"mapType": "roadmap", "language": "en-UK", "region": "UK"}'

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def fetchtile(x, y, zoom, f):
    global resp
    maxz = 2**zoom

    def inrange(v, mx):
        return v >= 0 and v < mx

    if not (inrange(x, maxz) and inrange(y, maxz)):
        return False
    url = "https://tile.googleapis.com/v1/2dtiles/{}/{}/{}?session={}&key={}&orientation=0".format(zoom, x, y, session, GOOGLE_KEY )
    resp = request("GET", url)
    if resp.status_code == 200:
        f.write(resp.content)
        f.close()
    return resp.status_code == 200


def centre_text(str, font, x, y, c):
    global g
    g.setfont(font)
    g.setfontalign(0, -1)
    g.text(str, x, y, c)


def makelevel(zoom):
    try:
        os.mkdir("/sd/gtiles/{}".format(zoom))
    except:
        pass


def makedir(tilex, zoom):
    try:
        os.mkdir("/sd/gtiles/{}/{}".format(zoom, tilex))
    except:
        pass


def openfile(tilex, tiley, zoom):
    try:
        return open("/sd/gtiles/{}/{}/{}.png".format(zoom, tilex, tiley), "xb")
    except:
        return None


def getTiles():
    global session, maptype
    resp = post('https://tile.googleapis.com/v1/createSession?key={}'.format(GOOGLE_KEY),
                    headers={'Content-Type': 'application/json'}, data = maptype).json()
    session=resp['session']
    print(session)
    count = 0
    loc, zoom = get_location()
    makelevel(zoom)
    xy = deg2num(loc[0], loc[1], zoom)
    for y in range(-1, 2):
        for x in range(-1, 2):
            tilex = xy[0] + x
            tiley = xy[1] + y
            status.update("{}.{}".format(tilex, tiley))
            makedir(tilex, zoom)
            f = openfile(tilex, tiley, zoom)
            if f is not None:
                resp = fetchtile(tilex, tiley, zoom, f)
                count += 1
                progress.update(str(count))
            else:
                progress.update("C")


def get_tiles():
    global status, progress
    do_connected_action(getTiles, status, progress)


def gen_map():
    gen_raw__tiles()
    combine_tiles()


update = Button("Fetch", 80, 180, 80, 40, roboto24)
buttons = ButtonMan()
buttons.add(update)
update.callback(get_tiles)


def app_init():
    global buttons
    centre_text("Google Tiles", roboto24, 120, 4, WHITE)
    status.update("Idle")
    progress.update("")
    buttons.start()


def app_end():
    buttons.stop()
    g.fill(BLACK)
