from machine import Pin


class Encoder:
    def __init__(self, pa, pb, cb):
        self.pinA = Pin(pb, Pin.IN, Pin.PULL_UP)
        self.pinB = Pin(pa, Pin.IN, Pin.PULL_UP)
        self.a0 = self.pinA.value()
        self.c0 = self.pinB.value()
        self.incr0 = 0
        self.second = False
        self.cb = cb
        self.pinA.irq(self.handler, Pin.IRQ_FALLING | Pin.IRQ_RISING)

    def handler(self, q):
        a = self.pinA.value()
        b = self.pinB.value()
        if a != self.a0:
            self.a0 = a
            if b != self.c0:
                self.c0 = b
                incr = -1 if (a == b) else 1
                if incr != self.incr0 or not self.second:
                    self.cb(incr)
                self.incr0 = incr
                self.second = not self.second


"""               
def test(inc):
    print("Encoder: ",inc)   
enc = Encoder(16,17,test)
"""
