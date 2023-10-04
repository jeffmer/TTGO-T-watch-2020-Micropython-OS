from machine import Pin, SPI, I2C, RTC
from drivers.pcf8563 import PCF8563
import time

I2C1 = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)

prtc = PCF8563(I2C1, None)
rtc = RTC()

dt = prtc.datetime()
print(dt)

epoch_secs = time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], dt[3], 0))

print(epoch_secs)

tm = time.gmtime(
    epoch_secs + 1 * 3600 + 3600
)

print(tm)
rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
