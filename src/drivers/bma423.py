# BMA423 Acceleometer
from micropython import const, schedule
from time import sleep_ms
from bma_config import bma_blob
from machine import Pin, SLEEP
from scheduler import Event
from config import VERSION


@micropython.viper
def conv(lo: int, hi: int) -> int:
    i = (hi << 8) + lo
    return ((i & 0x7FFF) - (i & 0x8000)) >> 4


class BMA423(Event):
    def __init__(self, i2c, ap):
        super().__init__()
        self.i2c = i2c
        self.ap = ap
        self.temp = bytearray(2)
        self.one = bytearray(1)
        self.init_blob()

    def init_blob(self):
        self.writeByte(0x7E, 0xB6)
        sleep_ms(10)
        self.writeByte(0x7C, 0x00)
        sleep_ms(1)
        self.writeByte(0x59, 0x00)
        mv = memoryview(bma_blob)
        for i in range(0, len(bma_blob), 16):
            self.writeByte(0x5B, (i // 2) & 0x0F)
            self.writeByte(0x5C, (i // 2) >> 4)
            self.i2c.writevto(0x19, (b"\x5E", mv[i : (i + 16)]))
        self.writeByte(0x59, 0x01)
        sleep_ms(200)
        # print("status ",self.readBytes(0x2A,1)[0])
        self.writeByte(0x7D, 0x04)
        self.writeByte(0x41, 0x00)  # 2g range
        self.writeByte(0x40, 0x17)
        self.writeByte(0x7C, 0x03)

    def writeByte(self, a, d):
        self.temp[0] = a
        self.temp[1] = d
        self.i2c.writeto(0x19, self.temp)

    def readBytes(self, a, n):
        self.one[0] = a
        self.i2c.writeto(0x19, self.one)
        return self.i2c.readfrom(0x19, n)

    def read(self):
        a = self.readBytes(0x12, 6)
        return (conv(a[0], a[1]), conv(a[2], a[3]), conv(a[4], a[5]))

    def configRead(self, len, offset):
        self.writeByte(0x7C, 0x00)  # disable sleep mode
        sleep_ms(1)
        res = bytearray(len)
        mv = memoryview(res)
        for i in range(0, len, 16):
            self.writeByte(0x5B, (offset + (i // 2)) & 0x0F)
            self.writeByte(0x5C, (offset + (i // 2)) >> 4)
            self.i2c.writeto(0x19, b"\x5E")
            self.i2c.readfrom_into(0x19, mv[i : (i + 16)])
        self.writeByte(0x7C, 0x03)  # enable sleep mode
        return res

    def configWrite(self, data, offset):
        self.writeByte(0x7C, 0x00)  # disable sleep mode
        sleep_ms(1)
        mv = memoryview(data)
        for i in range(0, len(data), 16):
            self.writeByte(0x5B, (offset + (i // 2)) & 0x0F)
            self.writeByte(0x5C, (offset + (i // 2)) >> 4)
            self.i2c.writevto(0x19, (b"\x5E", mv[i : (i + 16)]))
        self.writeByte(0x7C, 0x03)  # enable sleep mode

    def isr(self, p):
        self.irq_signal(self.readBytes(0x1C, 1))
        p.enable()

    # also enables double tap
    def wristInit(self):
        feature = self.configRead(0x46, 256)
        feature[0x3E] = 0x01  # double tap enable + sensitivity == 0 high
        feature[0x40] = feature[0x40] | 0x01  # wrist wear wakeup
        feature[0x45] = 1  # z_sign =1 invert z axis
        if VERSION == 1 or VERSION == 3:
            feature[0x44] = 0x8A  # z =2, y_sign =0, y=1, x_sign=1 x =0
        elif VERSION == 2:
            feature[0x44] = 0x81  # z =2, y_sign =0, y=0, x_sign=0 x =1
        self.configWrite(feature, 256)
        self.ap.irq(self.isr, Pin.IRQ_LOW_LEVEL, wake=SLEEP)
        self.readBytes(0x1C, 1)  # clear any previous motion interrupt
        self.writeByte(0x56, 0x18)  # map wrist and double tap interrupt to INT 1
        self.writeByte(0x53, 0x08)  # enable INT 1 output

    def stepInit(self):
        feature = self.configRead(0x46, 256)
        feature[0x3B] = 0x34
        # 0x3A+1
        self.configWrite(feature, 256)

    def totalSteps(self):
        res = self.readBytes(0x1E, 4)
        return (res[3] << 24) + (res[2] << 16) + (res[1] << 8) + res[0]
