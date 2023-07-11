from tempos import g
from graphics import WHITE, BLACK, YELLOW
from fonts import roboto18, roboto24, roboto36
from button import Button, ButtonMan
import time
import png
from widgets import Label
from wifi import do_connected_action
from urequests import request
import math
import json

status = Label(10, 80, 180, 40, roboto24, YELLOW)
progress = Label(200, 80, 40, 40, roboto24, YELLOW)


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def fetchtile(x, y, zoom, fn):
    global resp
    url = "https://tile.openstreetmap.de/{}/{}/{}.png".format(zoom, x, y)
    resp = request("GET", url)
    if resp.status_code == 200:
        status.update("Saving file")
        with open(fn, "wb") as f:
            f.write(resp.content)
            f.close()
    return resp.status_code == 200


def centre_text(str, font, x, y, c):
    global g
    g.setfont(font)
    g.setfontalign(0, -1)
    g.text(str, x, y, c)


def getTiles():
    loc = json.loads(open("location.json").read())
    xy = deg2num(loc["lat"], loc["long"], 16)
    count = 0
    for y in range(-1, 2):
        for x in range(-1, 2):
            tilex = xy[0] + x
            tiley = xy[1] + y
            resp = fetchtile(tilex, tiley, 16, "/sd/maps/t{}.png".format(count))
            progress.update(str(count))
            count += 1
            time.sleep(1)


def gen_raw__tiles():
    status.update("Gen raw file")
    for i in range(9):
        progress.update(str(i))
        png.saveRaw("/sd/maps/t{}.png".format(i), "/sd/maps/t{}.raw".format(i))
    status.update("Done")
    progress.update(" ")


def combine_tiles():
    N = 3
    status.update("Combine tiles")
    outfile = open("/sd/maps/map.raw", "wb")
    for row in range(N):
        files = []
        for i in range(N):
            fn = "/sd/maps/t{}.raw".format(row * N + i)
            files.append(open(fn, "rb"))
        for y in range(256):
            for x in range(N):
                pos = files[x].seek(y * 512)
                buf = files[x].read(512)
                outfile.write(buf)
        for i in range(N):
            files[i].close()
    outfile.close()
    status.update("Done")


def get_tiles():
    global status, progress
    do_connected_action(getTiles, status, progress)


def gen_map():
    gen_raw__tiles()
    combine_tiles()


update = Button("Fetch", 20, 180, 80, 40, roboto24)
genmap = Button("Gen Map", 120, 180, 100, 40, roboto24)
buttons = ButtonMan()
buttons.add(update)
buttons.add(genmap)
update.callback(get_tiles)
genmap.callback(gen_map)


def app_init():
    global buttons
    centre_text("Get Map", roboto36, 120, 4, WHITE)
    status.update("Idle")
    progress.update("")
    buttons.start()


def app_end():
    buttons.stop()
    g.fill(BLACK)
