from machine import Pin, SPI, I2C, RTC, Timer, lightsleep, wake_reason, SLEEP
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

from scheduler import Scheduler
from graphics import WHITE, BLACK
from time import sleep_ms, ticks_us, ticks_diff
from fonts import roboto18, roboto24
import esp32
import micropython
import time
from config import VERSION, summertime, timezone, battery_unit
import json


class Settings:
    def __init__(self, bright=0.3, ontime=20, clicking=False, buzzing=True):
        self._change = False
        try:
            self._set = json.loads(open("settings.json").read())
        except:
            self._set = {
                "bright": bright,
                "ontime": ontime,
                "timezone": timezone,
                "clicking": clicking,
                "buzzing": buzzing,
                "dst": summertime,
                "battery_unit": battery_unit,
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
    def battery_unit(self):
        return self._set["battery_unit"]

    @battery_unit.setter
    def battery_unit(self, v):
        self._set["battery_unit"] = v
        self._change = True


settings = Settings()

# power management


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


def set_local_time():
    epoch_secs = time.time()
    tm = time.gmtime(
        epoch_secs + settings.timezone * 3600 + (3600 if settings.dst else 0)
    )
    rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))


set_local_time()

# touch controller
tprst = Pin(47, Pin.OUT, value=1)
I2C0 = I2C(0, scl=Pin(41), sda=Pin(42), freq=400000)
tp = Pin(48, Pin.IN)
tc = CST816(I2C0, tp,tprst)

count = settings.ontime  # awake time


def touched(tch):
    global count
    count = settings.ontime

sched = Scheduler()

def onplus(t):
    global sched
    sched.stop()
    
plus = Pin(4,Pin.IN)
plus.irq(onplus, Pin.IRQ_FALLING)


tc.addListener(touched)



def dolightsleep(e):
    global count
    count -= 1
    if count > 0:
        return
    g.sleep()
    g.bright(0)
    tc.hibernate()
    sleep_ms(100)
    lightsleep()
    sleep_ms(100)
    tc.reset()
    count = settings.ontime
    g.wake()
    g.bright(settings.brightness)



dosleep = sched.setInterval(1000, dolightsleep, sched)


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