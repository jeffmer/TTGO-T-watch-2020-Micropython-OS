import time
from wifi import connect, disconnect
import urequests as requests
import json
from micropython import const
from math import sin,cos,radians
from graphics import BLUE, RED, YELLOW, CYAN
from tempos import settings
from config import LONGTITUDE, LATITUDE

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
CLIENT_ID = 'client id'
CLIENT_SECRET = 'secret'

DATA = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

RADIUS     = 1.0

CallSign = const(0)
Country  = const(1)
Long  = const(2)
Lat  = const(3)
Alt  = const(4)
Landed  = const(5)
Speed  = const(6)
Heading  = const(7)


URL = ""

def setRadius(r):
    global RADIUS, LONGTITUDE, LATITUDE, URL
    RADIUS = r/60
    URL = "https://opensky-network.org/api/states/all?lamin={:.4f}&lomin={:.4f}&lamax={:.4f}&lomax={:.4f}".format(
              LATITUDE-RADIUS,LONGTITUDE-RADIUS,LATITUDE+RADIUS,LONGTITUDE+RADIUS
           )

setRadius(settings.radius)

TOKEN_REFRESH_MARGIN = 30

class TokenManager:
    def __init__(self):
        self.token = None
        self.expires_at = None
        
    def get_token(self):
        """Return a valid access token, refreshing automatically if needed."""
        if self.token and self.expires_at and time.time() < self.expires_at:
            return self.token
        return self._refresh()

    def _refresh(self):
        print("get new token")
        """Fetch a new access token from the OpenSky authentication server."""
        r = requests.post(
            TOKEN_URL,
            data = DATA,
            headers = HEADERS
        )
        if not r.status_code == 200:
            print("Token response:", r.status_code, r.text)
        data = r.json()
        self.token = data["access_token"]
        expires_in = data.get("expires_in",1800)
        self.expires_at = time.time() + expires_in - TOKEN_REFRESH_MARGIN
        return self.token

    def headers(self):
        """Return request headers with a valid Bearer token."""
        return {"Authorization":"Bearer {}".format(self.get_token())}


# Create a single shared instance for your script.
tokens = TokenManager()

def planecolor(alt):
    c = CYAN
    if alt<10000 and alt>5000:
        c = YELLOW
    elif alt<= 5000:
        c = RED
    return c

def degtopx(lon,lat):
    x = ((lon-LONGTITUDE+RADIUS)/(2 * RADIUS))*240
    y = 240 - ((lat-LATITUDE+RADIUS)/(2 * RADIUS))*240
    return int(x),int(y)

def pxAirPos(a,dt):
    dist = a[Speed]*dt
    lon = a[Long]
    lat = a[Lat]
    head = radians(a[Heading])
    c = planecolor(a[Alt])
    if a[Alt]<10000 and a[Alt]>5000:
        c = YELLOW
    elif a[Alt]<= 5000:
        c = RED
    if dt > 0.1:
        lon = lon + (dist * sin(head))/(111320.0 * cos(radians(lat)))
        lat = lat + (dist * cos(head))/111320.0
    x,y = degtopx(lon,lat)
    return (a[CallSign].strip(),x,y,head,c)


def getupdate():
    r = requests.get(
            URL,
            headers=tokens.headers()
        )
    dd = r.json()
    ac  = []
    for a in dd['states']:
        if not a[8]:
            ar = ('NONAME' if a[1]=='' else a[1],a[2],a[5],a[6],a[7],a[8],a[9],a[10])
            p = pxAirPos(ar,0)
            rx = p[1] - 120
            ry = p[2] - 120
            if rx*rx + ry*ry < 115*115 and ar[Alt]>20:
                ac.append(ar)
    r.close()
    return ac
    



              




