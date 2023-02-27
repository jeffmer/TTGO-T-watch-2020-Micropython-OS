from machine import UART
from tempos import pm,sched
from scheduler import Event
from drivers.axp202 import LD04
from time import sleep_ms
from micropyGPS import MicropyGPS

def conv(r):
    v = r[0]+r[1]/60
    return v if r[2]=='N' or r[2]=='E' else -v

class L67K(Event):

    def __init__(self):
        super().__init__()
        self.uart = UART(1, baudrate=9600, tx=26, rx=36, timeout=10)
        self.parser = MicropyGPS()
        self._lat = 0.0
        self._long = 0.0
        self._fix = False
        self._buf = bytearray(128)
        self._timer = None
        self._pos = None

    def power(self,on):
        pm.setPower(LD04,1 if on else 0)

    def init(self):
        sleep_ms(500)
        self.uart.write("$PCAS03,0,0,0,0,0,0,0,0,0,0,,,0,0*02\r\n")
        sleep_ms(5)
        # Initialize the L76K Chip, use GPS + GLONASS
        self.uart.write("$PCAS04,5*1C\r\n")
        sleep_ms(250)
        # only ask for GGA
        self.uart.write("$PCAS03,1,0,0,0,0,0,0,0,0,0,,,0,0*03\r\n")
        sleep_ms(250);
        # Switch to Vehicle Mode, since SoftRF enables Aviation < 2g
        self.uart.write("$PCAS11,3*1E\r\n")

    def _getandparsebuf(self):
        nb = self.uart.readinto(self._buf)
        if not nb is None:
            for i in range(0,nb):
                stat = self.parser.update(chr(self._buf[i]))
                if not stat is None:
                    print(stat) # debug
                    self._fix = self.parser.fix_stat
                    stat = None
                    if self._fix>0:
                        self._endupdate()

    def _endupdate(self):
        self.power(False)
        self._pos = (conv(self.parser.latitude),conv(self.parser.longitude))
        if not self._timer is None:
            sched.clearInterval(self._timer)
        self.signal(self._pos)

    def update(self):
        self.power(True)
        self.init()
        self._timer = sched.setInterval(1000,self._getandparsebuf)

    def cancel_update():
        self.power(False)
        if not self._timer is None:
            sched.cancelInterval(self._timer)

'''
gps = L67K()
gps.addListener(lambda p:print(p))
def test():
    gps.update()
    while gps._pos is None:
        sleep_ms(1000)
        gps._getandparsebuf()
'''
