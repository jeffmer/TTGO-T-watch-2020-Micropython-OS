from tempos import g
from time import ticks_ms, ticks_diff
import machine
from micropython import const

MAX = const(1280)
map = open("/sd/maps/ham.raw", "rb")


def drawmap(xoff, yoff):
    global map
    xoff = MAX - 240 if (xoff + 240) >= MAX else xoff
    yoff = MAX - 240 if (yoff + 240) >= MAX else yoff
    now = ticks_ms()
    saved = machine.freq()
    machine.freq(240000000)
    bufaddr = memoryview(g._buf)
    for y in range(240):
        map.seek(xoff * 2 + (y + yoff) * 2560)
        map.readinto(bufaddr[y * 480 : (y + 1) * 480], 480)
    g.updateMod(0, 0, 239, 239)
    g.show()
    machine.freq(saved)
    print(ticks_diff(ticks_ms(), now))
