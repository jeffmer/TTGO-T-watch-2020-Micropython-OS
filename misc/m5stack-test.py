from machine import Pin, SPI, lightsleep,SLEEP
from ili9341 import ILI9341
from graphics import WHITE, BLACK
from fonts import roboto18, roboto24
from time import sleep_ms

# lcd display
spi = SPI(2, 32000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
g = ILI9341(spi, dc=Pin(27, Pin.OUT), cs=Pin(14, Pin.OUT), rst=Pin(33,Pin.OUT),bl=Pin(32,Pin.OUT))
g.fill(BLACK)
g.setcolor(WHITE, BLACK)
g.setfont(roboto18)
g.text("Loading...", 40, 110)
g.show()
g.bright(0.2)


def isr(p):
    print("Interrupt ",p)
    
flag = False
def isr_exit(p):
    global flag
    print("Exiting....",p)
    flag = True

pa = Pin(39, Pin.IN)
pb = Pin(38, Pin.IN)
pc = Pin(37, Pin.IN)   

pa.irq(isr,Pin.IRQ_LOW_LEVEL,wake=SLEEP)
pb.irq(isr_exit,Pin.IRQ_LOW_LEVEL,wake=SLEEP)
pc.irq(isr,Pin.IRQ_LOW_LEVEL,wake=SLEEP)

while not flag:
    print('sleep')
    g.sleep()
    g.bright(0)
    sleep_ms(500)  # allow print to complete
    lightsleep()
    print('wake')
    g.wake()
    g.bright(0.2)
    sleep_ms(5000) # time to set pins back to high_level 
    pa.enable()
    pb.enable()
    pc.enable()
