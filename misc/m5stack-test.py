from machine import Pin, SPI
from ili9341 import ILI9341
from graphics import WHITE, BLACK
from fonts import roboto18, roboto24 
# lcd display
spi = SPI(2, 32000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
g = ILI9341(spi, dc=Pin(27, Pin.OUT), cs=Pin(14, Pin.OUT), rst=Pin(33,Pin.OUT),bl=Pin(32,Pin.OUT))
g.fill(BLACK)
g.setcolor(WHITE, BLACK)
g.setfont(roboto18)
g.text("Loading...", 40, 110)
g.show()
g.bright(0.3)

