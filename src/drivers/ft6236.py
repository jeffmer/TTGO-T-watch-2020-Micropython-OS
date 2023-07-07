# TOUCH CONTROLLER
from micropython import const, schedule
from machine import Pin
from scheduler import Event

TOUCH_DOWN = const(0)
TOUCH_UP = const(1)
SWIPE_LEFT = const(2)
SWIPE_RIGHT = const(3)
SWIPE_UP = const(4)
SWIPE_DOWN = const(5)


class FT6236(Event):
    def __init__(self, i2c, tp):
        super().__init__()
        self.i2c = i2c
        self.tp = tp
        _data = bytearray(16)
        self.temp = bytearray(2)
        self.one = bytearray(1)
        self.enable(1)  # continuous interrupts while touched
        self.monitorMode()
        self.tp.irq(self.isr, Pin.IRQ_FALLING)
        self.first = None
        self.next = (-1, -1)

    def writeByte(self, a, d):
        self.temp[0] = a
        self.temp[1] = d
        self.i2c.writeto(0x38, self.temp)

    def readBytes(self, a, n):
        self.one[0] = a
        self.i2c.writeto(0x38, self.one)
        return self.i2c.readfrom(0x38, n)

    def threshold(self, v):
        self.writeByte(0x80, v)

    def setMonitorTime(self, secs):
        self.writeByte(0x87, secs)

    def touched(self):
        b = self.readBytes(0x02, 1)[0]
        return 0 if b > 2 else b

    def getXY(self):
        self._data = self.readBytes(0x02, 5)
        t = self._data[0]
        if t > 2 or t == 0:
            return (-1, -1)
        return (
            ((self._data[1] & 0x0F) << 8) | self._data[2],
            ((self._data[3] & 0x0F) << 8) | self._data[4],
        )

    def enable(self, v):
        self.writeByte(0xA4, v)

    def monitorMode(self):
        self.writeByte(0xA5, 0)

    def hibernate(self):
        self.writeByte(0xA5, 3)

    def reset(self):
        self.enable(1)  # continuous interrupts while touched
        self.monitorMode()

    def _gest(self):
        dx = self.next[0] - self.first[0]
        dy = self.next[1] - self.first[1]
        ax = dx if dx > 0 else -dx
        ay = dy if dy > 0 else -dy
        gest = TOUCH_UP
        if ax < 30 and ay < 30:
            return TOUCH_UP
        elif ay > ax:
            return SWIPE_DOWN if dy > 0 else SWIPE_UP
        else:
            return SWIPE_RIGHT if dx > 0 else SWIPE_LEFT

    def isr(self, p):
        pt = self.getXY()
        if self.first is None:
            if pt[0] < 0:
                return
            else:
                self.first = pt
                self.irq_signal((pt[0], pt[1], TOUCH_DOWN, -1, -1))
        else:
            if pt[0] >= 0:
                self.next = pt
            else:
                tch = (
                    self.first[0],
                    self.first[1],
                    self._gest(),
                    self.next[0],
                    self.next[1],
                )
                self.first = None
                self.irq_signal(tch)
