import gc
from tempos import g
from graphics import rgb, WHITE, BLACK, GREY, CYAN, GREEN, LIGHTGREY, YELLOW
from fonts import roboto18, roboto24, roboto36
from button import RoundButton, ButtonMan, Theme
from widgets import Label
from wifi import do_connected_action
from config import GOOGLE_KEY
import network
import ubinascii
import json
import urequests as rq

OFFX = 0 if g.width<=240 else 40

status = Label(0, 200, 100, 30, roboto18, YELLOW)
progress = Label(110, 200, 30, 30, roboto18, YELLOW)

postheme = Theme(WHITE, LIGHTGREY, GREEN, LIGHTGREY, roboto24)
update = RoundButton("Update", 70+OFFX, 140, 100, 50, theme=postheme)


buttons = ButtonMan()
buttons.add(update)


def drawPos(sh=True):
    global gps, saved, updating
    g.fill_rect(OFFX, 50, 240, 80, BLACK)
    g.setfont(roboto24)
    p = json.loads(open("location.json").read())
    lat = p["lat"]
    lng = p["long"]
    col = WHITE
    g.setfontalign(-1, -1)
    g.text("Lat : {:.4f}".format(lat), 60+OFFX, 70, GREEN)
    g.text("Long: {:.4f}".format(lng), 60+OFFX, 95, GREEN)
    if sh:
        g.show()

def findDevice():
    global status
    def getWifiNetworks():
        wlan = network.WLAN(network.STA_IF)
        scanned = wlan.scan()
        output = []
        for n in scanned:
            mac = ubinascii.hexlify(n[1]).decode('ascii')
            mac = ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))
            output.append({"macAddress": mac, "signalStrength": n[3], "channel": n[2]})
        del scanned
        return json.dumps({'wifiAccessPoints': output})
    status.update("Scanning")
    wifis = getWifiNetworks()
    gc.collect()
    status.update("Requesting")
    coordsjson = rq.post('https://www.googleapis.com/geolocation/v1/geolocate?key={}'.format(GOOGLE_KEY),
                    headers={'Content-Type': 'application/json'}, data = wifis).json()
    s = json.dumps({"lat": coordsjson["location"]["lat"], "long": coordsjson["location"]["lng"]})
    with open("location.json", "w") as f:
        f.write(s)
        f.close()
    print(s)
    return

def doupdate():
    global status, progress
    do_connected_action(findDevice, status, progress)
    drawPos()

update.callback(doupdate)


def app_init():
    g.setfont(roboto36)
    g.setfontalign(0, -1)
    g.text("Location", g.width//2, 10, WHITE)
    drawPos(False)
    buttons.start()

def app_end():
    buttons.stop()
    g.fill(BLACK)

