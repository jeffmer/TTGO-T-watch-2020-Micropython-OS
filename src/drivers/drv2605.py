# Internal constants:
ADDR = const(0x5A)
REG_STATUS = const(0x00)
REG_MODE = const(0x01)
REG_RTPIN = const(0x02)
REG_LIBRARY = const(0x03)
REG_WAVESEQ1 = const(0x04)
REG_WAVESEQ2 = const(0x05)
REG_WAVESEQ3 = const(0x06)
REG_WAVESEQ4 = const(0x07)
REG_WAVESEQ5 = const(0x08)
REG_WAVESEQ6 = const(0x09)
REG_WAVESEQ7 = const(0x0A)
REG_WAVESEQ8 = const(0x0B)
REG_GO = const(0x0C)
REG_OVERDRIVE = const(0x0D)
REG_SUSTAINPOS = const(0x0E)
REG_SUSTAINNEG = const(0x0F)
REG_BREAK = const(0x10)
REG_AUDIOCTRL = const(0x11)
REG_AUDIOLVL = const(0x12)
REG_AUDIOMAX = const(0x13)
REG_RATEDV = const(0x16)
REG_CLAMPV = const(0x17)
REG_AUTOCALCOMP = const(0x18)
REG_AUTOCALEMP = const(0x19)
REG_FEEDBACK = const(0x1A)
REG_CONTROL1 = const(0x1B)
REG_CONTROL2 = const(0x1C)
REG_CONTROL3 = const(0x1D)
REG_CONTROL4 = const(0x1E)
REG_VBAT = const(0x21)
REG_LRARESON = const(0x22)

# User-facing mode value constants:
MODE_INTTRIG = 0x00
MODE_EXTTRIGEDGE = 0x01
MODE_EXTTRIGLVL = 0x02
MODE_PWMANALOG = 0x03
MODE_AUDIOVIBE = 0x04
MODE_REALTIME = 0x05
MODE_DIAGNOS = 0x06
MODE_AUTOCAL = 0x07
LIBRARY_EMPTY = 0x00
LIBRARY_TS2200A = 0x01
LIBRARY_TS2200B = 0x02
LIBRARY_TS2200C = 0x03
LIBRARY_TS2200D = 0x04
LIBRARY_TS2200E = 0x05
LIBRARY_LRA = 0x06



class DRV2605:

    def __init__(self,i2c):
        self.i2c=i2c
        self.bytebuf = bytearray(1)

    def click(self):
        self.wr_b(REG_MODE, 0x00)  # out of standby
        self.wr_b(REG_RTPIN, 0x00)  # no real-time-playback
        self.wr_b(REG_WAVESEQ1, 1)  # strong click
        self.wr_b(REG_WAVESEQ2, 0)
        self.wr_b(REG_LIBRARY,LIBRARY_TS2200A)
        self.wr_b(REG_GO, 1)  
        
    def wr_b(self, reg, val):
        self.bytebuf[0] = val
        self.i2c.writeto_mem(ADDR, reg, self.bytebuf)

    def rd_b(self, reg):
        self.i2c.readfrom_mem_into(ADDR, reg, self.bytebuf)
        return self.bytebuf[0]

    def play(self) -> None:
        self.wr_b(REG_GO, 1)

    def stop(self) -> None:
        self.wr_b(REG_GO, 0)

    def setMode(self,v):
        self.wr_b(REG_MODE,v)

    def setLib(self,v):
        self.wr_b(REG_LIBRARY,v)

    def setRTP(self,v):
        self.wr_b(0x02,v)
        
    def setSlot(self,slot,effect):
        self.wr_b(REG_WAVESEQ1+slot-1,effect)
        

    def click(self):
        self.setMode(0)  # out of standby, internal trigger
        self.setRTP(0)  # no real-time-playback
        self.setSlot(1,1)  # strong click
        self.setSlot(2,0)
        self.setLib(LIBRARY_TS2200A)
        self.play()  

    def buzz(self,v):
        self.setMode(5) # rtp playback
        self.setRTP(0x7F if v else 0x00) # max buzz strength
        if not v:
            self.setMode(0x85) # standby

'''
from machine import Pin,I2C
from time import sleep_ms
I2C1 = I2C(1,scl=Pin(22),sda=Pin(21),freq=400000)
drv = DRV2605(I2C1)
'''

    
