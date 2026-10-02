from machine import Pin, SPI, I2C, RTC, Timer, lightsleep, wake_reason, SLEEP
from graphics import BLACK, GREEN
from fonts import roboto18, roboto24
from drivers.st7789 import ST7789
from drivers.cst816t import CST816
import time


spi = SPI(2, 32000000, sck=Pin(38), mosi=Pin(39), miso=None)
g = ST7789(spi, dc=Pin(45, Pin.OUT), cs=Pin(21, Pin.OUT), bl=Pin(46),rst=None)
g.fill(BLACK)
g.setcolor(GREEN, BLACK)
g.setfont(roboto24)
g.text("Hello World", 40, 100)
g.show()
g.bright(0.5)

time.sleep_ms(500)

tprst = Pin(47, Pin.OUT, value=1)
# touch controller
I2C0 = I2C(0, scl=Pin(41), sda=Pin(42), freq=400000)
tp = Pin(48, Pin.IN)
tc = CST816(I2C0, tp,tprst)
g.fill(BLACK)
g.setcolor(GREEN, BLACK)
g.setfont(roboto24)
g.text("HELLO", 40, 100)
g.show()
    


