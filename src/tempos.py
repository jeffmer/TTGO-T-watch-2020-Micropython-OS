from machine import Pin, SPI, I2C, RTC, Timer, lightsleep, wake_reason, SLEEP
from drivers.axp202 import AXP202
from drivers.st7789 import ST7789
from drivers.pcf8563 import PCF8563
from drivers.ft6236 import (
    FT6236,
    SWIPE_RIGHT,
    SWIPE_LEFT,
    SWIPE_UP,
    SWIPE_DOWN,
    TOUCH_DOWN,
    TOUCH_UP,
)
from drivers.bma423 import BMA423
from drivers.drv2605 import DRV2605
from scheduler import Scheduler
from graphics import WHITE, BLACK
from time import sleep_ms, ticks_us, ticks_diff
from fonts import roboto18, roboto24
import esp32
import micropython
import time
from config import VERSION
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
                "timezone": 0,
                "clicking": clicking,
                "buzzing": buzzing,
                "dst": False,
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


settings = Settings()

# power management
pmp = Pin(35, Pin.IN)
I2C1 = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
pm = AXP202(I2C1, pmp)
pm.init()
pm.enableIRQ(0x44, 5)  # PEK press falling edge

# lcd display
spi = SPI(2, 32000000, sck=Pin(18), mosi=Pin(19), miso=Pin(23))

bl_pin = None

if VERSION == 1:
    bl_pin = 12
elif VERSION == 2:
    bl_pin = 25
elif VERSION == 3:
    bl_pin = 15

g = ST7789(spi, dc=Pin(27, Pin.OUT), cs=Pin(5, Pin.OUT), bl=Pin(bl_pin))
g.fill(BLACK)
g.setcolor(WHITE, BLACK)
g.setfont(roboto18)
g.text("Loading...", 40, 110)
g.show()
g.bright(settings.brightness)

# persistent real time clock
rtcp = Pin(37, Pin.IN)
prtc = PCF8563(I2C1, rtcp)  # GM time persistent clock
rtc = RTC()  # local clock


def set_local_time():
    dt = prtc.datetime()
    epoch_secs = time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], dt[3], 0))
    tm = time.gmtime(
        epoch_secs + settings.timezone * 3600 + (3600 if settings.dst else 0)
    )
    rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))


set_local_time()

# touch controller
I2C0 = I2C(0, scl=Pin(32), sda=Pin(23), freq=400000)
tp = Pin(38, Pin.IN)
tc = FT6236(I2C0, tp)

count = settings.ontime  # awake time


def touched(tch):
    global count
    count = settings.ontime


tc.addListener(touched)

# accelerometer
ap = Pin(39, Pin.IN)
ac = BMA423(I2C1, ap)
ac.stepInit()
ac.wristInit()

if VERSION == 1 or VERSION == 3:
    _motorpin = Pin(4, Pin.OUT)

    def motor(v):
        _motorpin.value(v)

elif VERSION == 2:
    drv = DRV2605(I2C1)

    def motor(v):
        drv.buzz(v)


def dolightsleep(e):
    global count
    count -= 1
    if count > 0:
        return
    g.sleep()
    g.bright(0)
    if VERSION == 1 or VERSION == 3:
        motor(False)  # make sure motor is off
    if VERSION == 2:
        tc.hibernate()
    pm.lowpower(True)
    sleep_ms(100)
    lightsleep()
    sleep_ms(100)
    pm.lowpower(False)
    if VERSION == 2:
        tc.reset()
    set_local_time()
    count = settings.ontime
    g.wake()
    g.bright(settings.brightness)


sched = Scheduler()
dosleep = sched.setInterval(1000, dolightsleep, sched)


# buzzer


class Buzzer:
    def __init__(self, motorfn, period=500, duty=40):
        self._motor = motorfn
        self._ticker = None
        self._period = period
        self._duty = duty

    def buzz(self):
        self._motor(True)
        sched.setTimeout(self._period * self._duty // 100, self._motor, False)

    def click(self):
        if settings.clicking:
            if VERSION == 1 or VERSION == 3:
                self._motor(True)
                self._motor(False)
            elif VERSION == 2:
                drv.click()

    def start(self):
        if settings.buzzing:
            self._ticker = sched.setInterval(self._period, self.buzz)

    def stop(self):
        if not (self._ticker is None):
            sched.clearInterval(self._ticker)


buzzer = Buzzer(motor)

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
