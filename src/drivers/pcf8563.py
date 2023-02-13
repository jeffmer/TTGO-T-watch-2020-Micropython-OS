# REAL TIME CLOCK
from machine import Pin
from scheduler import Event

def Bcd2Int(v):
    tmp = (v//16) * 10
    return (tmp + v%16)

def Int2Bcd(v):
    tmp =(v//10) *16
    return (tmp + v%10)

class PCF8563(Event):

    def __init__(self,i2c,rtcp):
        super().__init__()
        self.i2c=i2c
        self.rtcp=rtcp
        self.bytebuf = bytearray(1)
        self.rtcp.irq(self.isr,Pin.IRQ_FALLING)
        self.enable_interrupt(True)
        
    def wr_b(self, reg, val):
        self.bytebuf[0] = val
        self.i2c.writeto_mem(0x51, reg, self.bytebuf)

    def rd_b(self, reg):
        self.i2c.readfrom_mem_into(0x51, reg, self.bytebuf)
        return self.bytebuf[0]

    def datetime(self):
        secs = Bcd2Int(self.rd_b(2)&0x7f)
        mins = Bcd2Int(self.rd_b(3)&0x7f)
        hrs = Bcd2Int(self.rd_b(4)&0x3f)
        day = Bcd2Int(self.rd_b(5)&0x3f)
        dofw = Bcd2Int(self.rd_b(6)&0x07)
        month = Bcd2Int(self.rd_b(7)&0x1f) 
        year= Bcd2Int(self.rd_b(8)&0x7f)+2000
        return (year,month,day,dofw,hrs,mins,secs,0)

    def set_datetime(self,t):
        self.wr_b(2,Int2Bcd(t[6]))
        self.wr_b(3,Int2Bcd(t[5]))
        self.wr_b(4,Int2Bcd(t[4]))
        self.wr_b(5,Int2Bcd(t[2]))
        self.wr_b(6,Int2Bcd(t[3]))
        self.wr_b(7,Int2Bcd(t[1]))
        self.wr_b(8,Int2Bcd(t[0])%100)

    def set_alarm(self, minute=None, hour=None, day=None, weekday=None):
        def f(v):
            return 0x80 if v is None else Int2Bcd(v) & 0x7f
        self.wr_b(9,f(minute))
        self.wr_b(10,f(hour))
        self.wr_b(11,f(day))
        self.wr_b(12,f(weekday))

    def clear_alarm(self):
        status = self.rd_b(1)
        self.wr_b(1,status &0xF7) #clear Alarm Flag bit 3 
        for r in range(9,13):
            self.wr_b(r,self.rd_b(r) | 0x80)

    def read_alarm(self):
        min_reg =  self.rd_b(9)
        hrs_reg =  self.rd_b(10)
        alarmed = bool(self.rd_b(1)&0x08)
        cleared = bool(min_reg & 0x80) and bool(hrs_reg & 0x80)
        retcode = 0 if cleared else 2 if alarmed else 1
        return retcode, Bcd2Int(min_reg & 0x7f), Bcd2Int(hrs_reg & 0x3f),
        
    def enable_interrupt(self,v):
        status = self.rd_b(1)
        self.wr_b(1,status | 0x02 if v else status & 0xFD)

    def isr(self,p):
        self.irq_signal(0)





