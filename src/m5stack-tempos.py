from machine import Pin, SPI, I2C, RTC, Timer, lightsleep, wake_reason, SLEEP
from drivers.axp192 import AXP192
from drivers.ili9341 import ILI9341
from drivers.pcf8563 import PCF8563
from drivers.ft6336 import (
    FT6336,
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
    def __init__(self, bright=0.3, ontime=20, timezone=0,clicking=False, buzzing=True, flashing=True, summertime=True,battery_unit="Volt"):
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
                "flashing": flashing,
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
    def flashing(self):
        return self._set["flashing"]

    @flashing.setter
    def flashing(self, v):
        self._set["flashing"] = v
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
I2C1 = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
pmp = Pin(35, Pin.IN)
pm = AXP192(I2C1,pmp)
pm.init()
pm.enableIRQ(0x42, 1)  # PEK press falling edge

#def pressed(tch):
#   print(tch)
    
#pm.addListener(pressed)

# lcd display
spi = SPI(2, 32000000, sck=Pin(18), mosi=Pin(23), miso=Pin(38))
g = ILI9341(spi, dc=Pin(15, Pin.OUT), cs=Pin(5, Pin.OUT),bl=pm.bright)
g.fill(BLACK)
g.setcolor(WHITE, BLACK)
g.setfont(roboto18)
g.text("Loading...", 40, 110)
g.show()
pm.bright(0.5)

#SD card
try:
    import sdcard, os
    sd = sdcard.SDCard(spi, Pin(4,))
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")
except Exception as e:
    spi.init(baudrate=32000000) # reset slow spi rate used by SDCard
    g.text("NO SD Card", 40,130)
    g.show()
    
# persistent real time clock
prtc = PCF8563(I2C1, None)  # GM time persistent clock
rtc = RTC()  # local clock

def set_local_time():
    dt = prtc.datetime()
    epoch_secs = time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], dt[3], 0))
    try:
        tm = time.gmtime(
            epoch_secs + settings.timezone * 3600 + (3600 if settings.dst else 0)
        )
        rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
    except:
        pass


set_local_time()

# touch controller
tp = Pin(39, Pin.IN)
tc = FT6336(I2C1, tp)

count = settings.ontime  # awake time


def touched(tch):
    global count
    count = settings.ontime

tc.addListener(touched)


def motor(v):
    pm.buzz(v)

def dolightsleep(e):
    global count
    count -= 1
    if count > 0:
        return
    g.sleep()
    pm.bright(0)
    motor(False)  # make sure motor is off
    pm.lowpower(True)
    sleep_ms(100)
    lightsleep()
    sleep_ms(100)
    pm.lowpower(False)
    set_local_time()
    count = settings.ontime
    g.wake()
    g.bright(settings.brightness)


sched = Scheduler()
dosleep = sched.setInterval(1000, dolightsleep, sched)


# buzzer
class Buzzer:
    def __init__(self, motorfn, flashfn, period=500, duty=40):
        self._motor = motorfn
        self._flash = flashfn
        self._ticker = None
        self._period = period
        self._duty = duty


    def both(self,v):
        if settings.buzzing:
            self._motor(v)
        if settings.flashing:
            self._flash(v)
        
    def buzzflash(self):
        self.both(True)
        sched.setTimeout(self._period * self._duty // 100, self.both, False)
        
    def click(self):
        if settings.clicking:
            if VERSION == 1 or VERSION == 3:
                self._motor(True)
                sleep_ms(30)
                self._motor(False)
            elif VERSION == 2:
                drv.click()
        
    def start(self):
        if settings.buzzing or settings.flashing:
            self._ticker = sched.setInterval(self._period, self.buzzflash)

    def stop(self):
        if self._ticker is not None:
            sched.clearInterval(self._ticker)


buzzer = Buzzer(motor,pm.setLED)


