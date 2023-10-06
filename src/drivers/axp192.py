from micropython import const
from machine import Pin, SLEEP
from time import sleep_ms
from scheduler import Event

EXTEN = const(0x06)
DCDC2 = const(0x04)
LDO3 = const(0x03)
LDO2 = const(0x02)
DCDC3 = const(0x01)
DCDC1 = const(0x00)

class AXP192(Event):
    def __init__(self, i2c,pmp):
        super().__init__()
        self.i2c = i2c
        self._pmp=pmp
        self.one = bytearray(1)
        # disable all interrupts
        for a in range(0x40, 0x44):
            self.writeByte(a, 0)
        self.clearIRQ()
        self._pmp.irq(self.isr, Pin.IRQ_LOW_LEVEL, wake=SLEEP)

    def writeByte(self, a, d):
        self.one[0]=d
        self.i2c.writeto_mem(0x34, a, self.one)

    def readByte(self, a):
        return self.i2c.readfrom_mem(0x34, a,1)[0]
    
    def clearIRQ(self):
        self.i2c.writeto(0x34, b"\x44")
        status = self.i2c.readfrom(0x34, 5)
        for a in range(0x44, 0x48):
            self.writeByte(a, 0xFF)
        return status

    def enableIRQ(self, reg, bit):
        v = self.readByte(reg)
        v = v | 1 << bit
        self.writeByte(reg, v)

    def isr(self, p):
        self.irq_signal(self.clearIRQ())
        p.enable()

    def batV(self):
        d = self.i2c.readfrom_mem(0x34, 0x78, 2)
        v = d[0] * 16 + d[1]
        ADCLSB = 1.1 / 1000.0
        return v * ADCLSB
    
    def batChargeA(self):
        hv = self.readByte(0x7A)
        lv = self.readByte(0x7B)
        return ((hv << 4) | (lv & 0x0F)) // 2

    def batDisChargeA(self):
        hv = self.readByte(0x7C)
        lv = self.readByte(0x7D)
        return ((hv << 5) | (lv & 0x1F)) // 2

    def batA(self):
        return self.batChargeA() - self.batDisChargeA()
    
    def batPercent(self):
        bv = self.batV()
        bp = 0 if bv<3.248088 else int((bv-3.120712)*100)
        return bp if bp<=100 else 100

    def setExtenCtl(self,v):
        d = self.readByte(0x10)
        self.writeByte(0x10,d|0x04 if v else d & 0xFB)

    def setGPIO1(self, v):
        self.writeByte(0x92,0)
        d = self.readByte(0x94)
        self.writeByte(0x94,d|0x02 if v else d&0xFD)
        
    def setGPIO2 (self, v):
        self.writeByte(0x93,0)
        d = self.readByte(0x94)
        self.writeByte(0x94,d|0x04 if v else d&0xFB)
        
    def setGPIO4(self, v):
        self.writeByte(0x95,0x84) #GPIO fn open drain output, asssume GPIO3 not used 
        d = self.readByte(0x94)
        self.writeByte(0x96,d|0x02 if v else d&0xFD)
        
    def setPower(self, bus, state):
        buf = self.readByte(0x12)
        data = (buf | 0x01 << bus) if state else (buf & ~(0x01 << bus))
        self.writeByte(0x12, data)

    def setDCDC1voltage(self,v):
        v = 112 if v>3500 else (v-700)//25
        self.writeByte(0x26,v&0x7F)

    def setDCDC3voltage(self,v):
        v = 112 if v>3500 else (v-700)//25
        self.writeByte(0x27,v&0x7F)
        
    def setLDO2voltage(self,v):
        v = 15 if v>3300 else (v-1800)//100
        self.writeByte(0x28,(self.readByte(0x28) & 0x0F)| (v<<4))
        
    def setLDO3voltage(self,v):
        v = 15 if v>3300 else (v-1800)//100
        self.writeByte(0x28,(self.readByte(0x28) & 0xF0)| v)
    
    def adc1Enable(self, en):
        # enable bits 7 bat voltage, 6 battery current, 1 APS V, 0, TS pin
        self.writeByte(0x82, 0xC3 if en else 0x00)
    
    def lcd_reset(self):
        self.setGPIO4(False)
        sleep_ms(10)
        self.setGPIO4(True)
        sleep_ms(100)
        
    def setLED(self,v):
        self.setGPIO1(not v)
        
    def init(self):
        self.setGPIO1(True) # turn off led
        self.setGPIO2(False) # disable amplifier
        self.setExtenCtl(False) # disable 5v boost 
        self.setLDO2voltage(3300)
        self.setPower(LDO2,True)
        self.adc1Enable(True)
        self.writeByte(0x33,0xC4) # set charging 4.2V, 280ma
        self.lcd_reset()
        
    def bright(self,v):
        if v<=0:
            self.setPower(DCDC3,False)
        else:
            v = 1 if v>1 else v
            self.setDCDC3voltage(2450 + int(v*850))
            self.setPower(DCDC3,True)
            
    def buzz(self,en,mv=2800):
        self.setLDO3voltage(mv)
        self.setPower(LDO3,en)
        
    def lowpower(self, b):
        if b:
            self.adc1Enable(False)
            self.setDCDC1voltage(2700)
        else:
            self.setDCDC1voltage(3300)
            self.adc1Enable(True)

