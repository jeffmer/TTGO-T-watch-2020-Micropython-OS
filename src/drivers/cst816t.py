# TOUCH CONTROLLER
from micropython import const, schedule
from machine import Pin
from scheduler import Event
from time import sleep_ms 

SWIPE_UP = const(1)
SWIPE_DOWN = const(2)
SWIPE_LEFT = const(3)
SWIPE_RIGHT = const(4)
CLICK = const(5)
DOUBLE_CLICK = const(11)
LONG_PRESS = const(12)

TOUCH_DOWN = const(0)
TOUCH_UP = const(-1)

class CST816(Event):
    def __init__(self, i2c, tp, rst=None):
        super().__init__()
        self.i2c = i2c
        self.tp = tp
        self.rst = rst
        if self.rst is not None:
            self.rst(0)
            sleep_ms(10)
            self.rst(1)
        sleep_ms(150)
        _data = bytearray(16)
        self.temp = bytearray(2)
        self.one = bytearray(1)
        self.enable()    
        self.tp.irq(self.isr, Pin.IRQ_FALLING)
        self.first = None
        self.next = (-1, -1)
        self._last_gest = 0
        self._e = Event()
        self._e.addListener(self.handler)
        

    def writeByte(self, a, d):
        self.temp[0] = a
        self.temp[1] = d
        self.i2c.writeto(0x15, self.temp)

    def readBytes(self, a, n):
        self.one[0] = a
        self.i2c.writeto(0x15, self.one)
        return self.i2c.readfrom(0x15, n)

    def touched(self):
        b = self.readBytes(0x02, 1)[0]
        return 0 if b > 2 else b

    def getXY(self):
        self._data = self.readBytes(0x00, 8)
        _gest = self._data[1]
        if _gest == 0 and self._data[2] == 0:
            _gest = TOUCH_UP      
        return (
            ((self._data[3] & 0x0F) << 8) | self._data[4],
            ((self._data[5] & 0x0F) << 8) | self._data[6],
            _gest
        )

    def enable(self):
        self.writeByte(0xFA, 0x31)  # interrupt on down and up)
        self.writeByte(0xEC, 0x00)

    def hibernate(self):
        self.writeByte(0xE5, 0x03)
        
    def reset(self):
        if self.rst is not None:
            self.rst(0)
            sleep_ms(10)
            self.rst(1)
        sleep_ms(150)
        self.enable()

    def isr(self, p):
        self._e.irq_signal(p)
        
    def handler(self,p):
        x = self.getXY()
        pt = self.getXY()
        if pt[2] == CLICK or self._last_gest >0 and pt[2]<0:
            pass
        else:
            self.signal(pt)
        self._last_gest = pt[2]
