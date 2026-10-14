from machine import Pin, SPI, I2C, RTC, Timer, lightsleep, wake_reason, SLEEP, freq
from drivers.st7789 import ST7789
from drivers.cst816t import (
    CST816,
    SWIPE_RIGHT,
    SWIPE_LEFT,
    SWIPE_UP,
    SWIPE_DOWN,
    TOUCH_DOWN,
    TOUCH_UP,
)
from drivers.switch import Switch
from scheduler import Scheduler
from graphics import WHITE, BLACK
from time import sleep_ms, ticks_us, ticks_diff
from fonts import roboto18, roboto24
import esp32
import micropython
import time
from config import VERSION, summertime, timezone
import json


class Settings:
    def __init__(self, bright=0.3, radius=10, ontime=20, clicking=False, buzzing=True):
        self._change = False
        try:
            self._set = json.loads(open("settings.json").read())
        except:
            self._set = {
                "bright": bright,
                "radius": radius,
                "ontime": ontime,
                "timezone": timezone,
                "clicking": clicking,
                "buzzing": buzzing,
                "dst": summertime,
                "secs_per_hour_err": 0,
            }
            self.save()

    def save(self):
        if self._change:
            with open("settings.json", "w") as f:
                f.write(json.dumps(self._set))
                f.close()
            self._change = False

    @property
    def brightness(self):
        return self._set["bright"]

    @brightness.setter
    def brightness(self, br):
        self._set["bright"] = 0.1 if br < 0.1 else 1.0 if br > 1.0 else br
        self._change = True
        
    @property
    def radius(self):
        return self._set["radius"]

    @radius.setter
    def radius(self, br):
        self._set["radius"] = 5 if br < 5 else 120 if br > 120 else br
        self._change = True

    @property
    def ontime(self):
        return self._set["ontime"]

    @ontime.setter
    def ontime(self, br):
        self._set["ontime"] = 5 if br < 5 else 300 if br > 300 else br
        self._change = True

    @property
    def timezone(self):
        return self._set["timezone"]

    @timezone.setter
    def timezone(self, br):
        self._set["timezone"] = br
        self._change = True

    @property
    def clicking(self):
        return self._set["clicking"]

    @clicking.setter
    def clicking(self, v):
        self._set["clicking"] = v
        self._change = True

    @property
    def buzzing(self):
        return self._set["buzzing"]

    @buzzing.setter
    def buzzing(self, v):
        self._set["buzzing"] = v
        self._change = True

    @property
    def dst(self):
        return self._set["dst"]

    @dst.setter
    def dst(self, v):
        self._set["dst"] = v
        self._change = True

    @property
    def secs_per_hour_err(self):
        return self._set["secs_per_hour_err"]

    @secs_per_hour_err.setter
    def secs_per_hour_err(self, v):
        self._set["secs_per_hour_err"] = v
        self._change = True


settings = Settings()

# plus button

sw = Switch(4)

# lcd display
spi = SPI(2, 32000000, sck=Pin(38), mosi=Pin(39), miso=None)
g = ST7789(spi, dc=Pin(45, Pin.OUT), cs=Pin(21, Pin.OUT), bl=Pin(46),rst=None)
g.fill(BLACK)
g.setcolor(WHITE, BLACK)
g.setfont(roboto18)
g.text("Loading...", 40, 110)
g.show()
g.bright(settings.brightness)

rtc = RTC()  # local clock

# touch controller
tprst = Pin(47, Pin.OUT, value=1)
p_scl = Pin(41)
p_sda = Pin(42)
I2C0 = I2C(0, scl=p_scl, sda=p_sda, freq=400000)
tp = Pin(48, Pin.IN)

tc = CST816(I2C0, tp,tprst)

def set_local_time():
    epoch_secs = time.time()
    tm = time.gmtime(
        epoch_secs + settings.timezone * 3600 + (3600 if settings.dst else 0)
    )
    rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
    
def correct_local_time(err):
    epoch_secs = time.time()
    tm = time.gmtime(
        epoch_secs - err
    )
    rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))

sched = Scheduler()

count = settings.ontime  # awake time

_cansleep = True

sleep_start = 0

def recalibrateRTC():
    global sleep_start
    sleep_end = time.time()
    e = int(((sleep_end - sleep_start)*settings.secs_per_hour_err)/3600)
    correct_local_time(e)

def touched(tch):
    global count
    count = settings.ontime


tc.addListener(touched)

pactrl = Pin(7, Pin.OUT, value=0) # make sure power amp is off

def dolightsleep(e):
    global count, sleep_start
    count -= 1
    if count > 0:
        return
    sleep_start = time.time()
    tc.hibernate()
    g.sleep()
    g.bright(0)
    sleep_ms(100)
    lightsleep()
    sleep_ms(100)
    count = settings.ontime
    recalibrateRTC()
    g.wake()
    tc.reset()
    g.bright(settings.brightness)

dosleep = None

def enable_sleep():
    global dosleep
    dosleep = sched.setInterval(1000, dolightsleep, sched)

def disable_sleep():
    global dosleep
    sched.clearInterval(dosleep)
    

enable_sleep()

freq(160000000)



"""
# sd card && gps
if VERSION == 2:
    import os
    from machine import SDCard

    sd = SDCard(slot=3, sck=Pin(14), mosi=Pin(15), miso=Pin(4), cs=Pin(13))
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")

    from drivers.l67k import L67K

    gps = L67K()

# TODO: Support PCM mic for VERSION == 3
"""
