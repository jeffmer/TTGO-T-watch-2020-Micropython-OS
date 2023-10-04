from machine import Pin, I2C, SPI
from drivers.axp192 import AXP192,DCDC3,LDO2
from drivers.ili9341 import ILI9341
from graphics import BLACK, WHITE, GREEN
from fonts import roboto18, roboto24, roboto36
import math
from time import sleep_ms

i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)

pm = AXP192(i2c)
pm.init()
print(pm.batV(),"V")
print(pm.batA(),"ma")


# lcd display
spi = SPI(2, 32000000, sck=Pin(18), mosi=Pin(23), miso=Pin(38))
g = ILI9341(spi, dc=Pin(15, Pin.OUT), cs=Pin(5, Pin.OUT))
g.fill(BLACK)
g.setcolor(WHITE, BLACK)
g.setfont(roboto18)
g.text("Loading...", 40, 110)
g.show()
pm.bright(0.5)


X = const(80)
Y = const(70)
batpercent = 50

def drawBat():
    g.fill(BLACK)
    global batpercent
    v = pm.batPercent()
    batpercent = v if v > 0 else batpercent
    g.setfont(roboto36)
    g.setfontalign(0, -1)
    g.text("Battery", 120, 20, WHITE)
    g.fill_rect(X, Y, 80, 32, WHITE)
    g.fill_rect(X + 4, Y + 4, 72, 24, BLACK)
    g.fill_rect(X + 6, Y + 6, math.ceil(68 * batpercent / 100), 20, GREEN)
    g.fill_rect(X + 80, Y + 8, 4, 16, WHITE)
    g.setfont(roboto24)
    g.setfontalign(-1, -1)
    g.text("{:02}%".format(batpercent), X, Y + 42)
    g.text("{:.1f}ma".format(-pm.batA()), X, Y + 72)
    g.text("{:.2f}V".format(pm.batV()), X, Y + 102)
    g.show()


while True:
    sleep_ms(1000)
    drawBat()
