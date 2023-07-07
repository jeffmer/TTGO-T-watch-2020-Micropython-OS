from tempos import g, gps
from graphics import rgb, WHITE, BLACK, GREY, CYAN, GREEN, LIGHTGREY, YELLOW
from fonts import roboto24, roboto36
from button import RoundButton, ButtonMan, Theme
import json

postheme = Theme(WHITE, LIGHTGREY, GREEN, LIGHTGREY, roboto24)

update = RoundButton("Update", 10, 130, 100, 50, theme=postheme)
cancel = RoundButton("Cancel", 10, 190, 100, 50, theme=postheme)
save = RoundButton("Save", 140, 190, 100, 50, theme=postheme)

buttons = ButtonMan()
buttons.add(update)
buttons.add(cancel)
buttons.add(save)

saved = False
updating = False


def drawPos(sh=True):
    global gps, saved, updating
    g.fill_rect(0, 50, 240, 80, BLACK)
    g.setfont(roboto24)
    if not gps._pos is None:
        lat = gps._pos[0]
        lng = gps._pos[1]
        col = YELLOW
    else:
        p = json.loads(open("location.json").read())
        lat = p["lat"]
        lng = p["long"]
        col = WHITE
    g.setfontalign(-1, -1)
    g.text("Lat : {:.4f}".format(lat), 60, 50, GREEN if saved else col)
    g.text("Long: {:.4f}".format(lng), 60, 75, GREEN if saved else col)
    g.setfontalign(0, -1)
    if not gps.updating():
        g.text("GPS OFF", 120, 105, CYAN)
    elif not updating:
        g.text("GPS ON", 120, 105, GREEN)
    else:
        g.text("Updating", 120, 105, YELLOW)
    if sh:
        g.show()


def doupdate():
    global saved
    saved = False
    gps.update()
    drawPos()


def docancel():
    updating = False
    gps.cancel_update()
    drawPos()


def dosave():
    global saved
    saved = True
    drawPos()
    if not gps._pos is None:
        s = json.dumps({"lat": gps._pos[0], "long": gps._pos[1]})
        with open("location.json", "w") as f:
            f.write(s)
            f.close()
        print(s)


update.callback(doupdate)
cancel.callback(docancel)
save.callback(dosave)


def onUpdate(pos):
    global updating
    updating = True
    drawPos()


listener = None


def app_init():
    global listener
    g.setfont(roboto36)
    g.setfontalign(0, -1)
    g.text("Position", 120, 10, WHITE)
    drawPos(False)
    listener = gps.addListener(onUpdate)
    buttons.start()


def app_end():
    global gpslistener
    buttons.stop()
    g.fill(BLACK)
    if not listener is None:
        gps.removeListener(listener)
