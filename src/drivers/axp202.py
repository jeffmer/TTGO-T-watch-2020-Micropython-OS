from micropython import const
from machine import Pin,SLEEP
from time import sleep_ms
from config import VERSION
from scheduler import Event

LD02 = const(0x02)
EXTEN =  const(0x00)
DCDC2 = const(0x04)
LD04 = const(0x03)
LD03 = const(0x06)

class AXP202(Event):

    def __init__(self,i2c,pmp):
        super().__init__()
        self.i2c = i2c
        self.temp = bytearray(2)
        self.one = bytearray(1)
        self._pmp = pmp
        # disable all interrupts
        for a in range(0x40,0x45):
            self.writeByte(a,0)
        self.clearIRQ()
        self._pmp.irq(self.isr,Pin.IRQ_LOW_LEVEL,wake=SLEEP)

    def writeByte(self,a,d):
        self.temp[0] = a
        self.temp[1] = d
        self.i2c.writeto(0x35,self.temp)

    def readByte(self,a):
        self.one[0] = a
        self.i2c.writeto(0x35,self.one)
        return self.i2c.readfrom(0x35,1)[0]

    def clearIRQ(self):
        self.i2c.writeto(0x35,b'\x48')
        status = self.i2c.readfrom(0x35,5)
        for a in range(0x48,0x4D):
            self.writeByte(a,0xFF)
        return status

    def enableIRQ(self,reg,bit):
        v = self.readByte(reg)
        v = v | 1<<bit
        self.writeByte(reg,v)


    def isr(self,p):
        self.irq_signal(self.clearIRQ())
        p.enable()


    def setPower(self,bus,state):
        buf = self.readByte(0x12)
        data = (buf | 0x01<<bus) if state else (buf & ~(0x01<<bus))
        if (state):
            data|=2 #AXP202 DCDC3 force
        self.writeByte(0x12,data)

    def setCharge(self,ma):
        val = self.readByte(0x33)
        val = val & 0b11110000
        ma = ma - 300
        val = val | (ma // 100)
        self.writeByte(0x33, val)

    def setLEDoff(self):
        val = self.readByte(0x32)
        val = val & 0b11001111
        val = val | 0x08
        self.writeByte(0x32, val)

    def adc1Enable(self,mask,en):
        val = self.readByte(0x82)
        val = val|mask if en else val & ~mask
        self.writeByte(0x82,val)

    def setLD03Mode(self,m):
        val = self.readByte(0x29)
        if (m):
            val|=0x80
        else:
            val&=0x7F;
        self.writeByte(0x29,val)

    def setDCDC3Voltage(self,mv):
        if (mv<700 or mv>3500):
             return
        val = (mv-700)//25
        self.writeByte(0x27,val)

    def setGPIO0(self,v):
        val = self.readByte(0x90)
        val &= 0xF8
        val |= 1 if v else 0
        self.writeByte(0x90,val)

    def batV(self):
        self.one[0]=0x78
        self.i2c.writeto(0x35,self.one)
        d = self.i2c.readfrom(0x35,2)
        v = d[0]*16+d[1]
        ADCLSB = 1.1 / 1000.0
        return v * ADCLSB

    def batPercent(self):
        v = self.readByte(0xB9)
        if not (v & 0x80):
             v &= 0x7F
             return v if v<=100 else 0
        return 0

    def batChargeA(self):
        hv = self.readByte(0x7A)
        lv = self.readByte(0x7B)
        return ((hv << 4) | (lv & 0x0F))//2

    def batDisChargeA(self):
        hv = self.readByte(0x7C)
        lv = self.readByte(0x7D)
        return ((hv << 5) | (lv & 0x1F))//2

    def batA(self):
        return self.batChargeA() - self.batDisChargeA();

    def supplyA(self):
        hv = self.readByte(0x5C)
        lv = self.readByte(0x5D)
        return (((hv << 4) | (lv & 0x0F)) * 3)//8

    def init(self):
        self.setLEDoff()
        self.setCharge(300) # 300 ma is min max  charge
        self.setPower(LD02,1)   # back light power on
        self.setLD03Mode(1)
        self.setPower(DCDC2,0)
        self.adc1Enable(0xCD,True)
        if VERSION==1:
            self.setPower(EXTEN,0)
            self.setPower(LD03,0)
        if VERSION==3:
            self.setPower(EXTEN,0)
            self.setPower(LD04,0)
        else:
            self.setPower(EXTEN,1) # touch reset
            self.setPower(LD03,1)   #tft/touch
            self.setGPIO0(True)  # enable DRV2605L motor driver
            self.setPower(LD04,0)   #gps

    def lowpower(self,b):
        if b:
            self.adc1Enable(0xCD,False)
            self.setPower(LD02,0)
            if VERSION ==2:
                self.setGPIO0(False)  # disable motor driver
            self.setDCDC3Voltage(2700)
        else:
            self.setDCDC3Voltage(3300)
            self.adc1Enable(0xCD,True)
            self.setPower(LD02,1)
            if VERSION ==2: # reset touch by pulsing EXTEN
                self.setPower(EXTEN,0) # touch reset
                sleep_ms(10)
                self.setPower(EXTEN,1) # touch reset
                self.setGPIO0(True) # enable motor driver



