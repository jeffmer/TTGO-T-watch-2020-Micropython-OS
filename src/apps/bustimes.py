import ure
import time
import requests
import time
import math
import wifi
from tempos import sched, settings, g, disable_sleep, enable_sleep, set_local_time
from graphics import rgb, WHITE, BLACK, RED, YELLOW
from fonts import roboto18, roboto24, roboto36
from wifi import connect, lazy_disconnect
from widgets import Label
import ntptime

_time_offset = settings.timezone * 3600 + (3600 if settings.dst else 0)
_bus_stop = "490009652N"
_bus_stop_name = "Mariner Gardens"

def parseDateTime(datestr):
    regex = "^(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z$"
    match = ure.match(regex, datestr)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        seconds = int(match.group(6))
        return time.mktime((year, month, day, hour, minute, seconds,0,0))
    else:
        return None
       
def getdelay(ts):
    global _time_offset
    at = parseDateTime(ts)
    if at is None:
        return None
    secs = at + _time_offset - time.time()
    return int(secs/60)


def bustimes(naptanId):
    URL = "https://api.tfl.gov.uk/StopPoint/{}/Arrivals".format(naptanId)
    r = requests.get(URL)       
    dd = r.json()
    res = []
    for el in dd:
        line = el["lineName"]
        dest = el["destinationName"]
        dest = (dest.split(","))[0]
        arrival = el["expectedArrival"]
        r = (line,dest,getdelay(arrival))
        res.append(r)
    res.sort(key=lambda e : e[2])
    return res
        

def draw_title(now):
    global _bus_stop, _bus_stop_name
    g.fill(BLACK)
    g.setfont(roboto24)
    g.fill_rect(0,0,240,40, RED)
    g.setfontalign(0, 0)
    g.text(_bus_stop_name, 120, 20, WHITE)
    if now:
        g.show()
        
def draw_all():
    global _bus_stop    
    draw_title(False)
    bt = bustimes(_bus_stop)
    y = 50
    g.setfont(roboto18)
    g.setfontalign(-1, -1)
    g.text("Bus",10,y,WHITE)
    g.setfontalign(0, -1)
    g.text("Destination",120,y,WHITE)
    g.setfontalign(1, -1)
    g.text("Min",230,y,WHITE)
    y +=30
    g.line(10,y,230,y,WHITE)
    y+=20
    g.setfont(roboto24)
    for b in bt:
        g.setfontalign(-1, -1)
        g.text(b[0],10,y,WHITE)
        g.setfontalign(0, -1)
        g.text(b[1],120,y,WHITE)
        g.setfontalign(1, -1)
        g.text(b[2]==0:"due":str(b[2]),230,y,WHITE)
        y+=40
    g.show()   
    
status = Label(20, 200, 160, 40, roboto18, YELLOW)
progress = Label(200, 200, 40, 40, roboto18, YELLOW)

_ticker = None

def app_init():
    global _ticker
    disable_sleep()   
    draw_title(True)
    connect(status,progress)
    ntptime.settime()
    set_local_time()
    draw_all()
    _ticker=sched.setInterval(30000,draw_all)
    


def app_end():
    global _ticker
    sched.clearInterval(_ticker)
    g.fill(BLACK)
    lazy_disconnect()
    enable_sleep()
   