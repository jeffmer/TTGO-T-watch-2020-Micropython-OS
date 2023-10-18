# ILI9341 nano-gui driver for ili9341 displays
# As with all nano-gui displays, touch is not supported.

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

# This work is based on the following sources.
# https://github.com/rdagger/micropython-ili9341
# Also this forum thread with ideas from @minyiky:
# https://forum.micropython.org/viewtopic.php?f=18&t=9368

from machine import PWM
from time import sleep_ms
import gc
import framebuf
from graphics import Graphics, COLOR_LUT

@micropython.viper
def _lcopy(dest:ptr16, source:ptr8, lut:ptr16, length:int):
    # rgb565 - 16bit/pixel
    n = 0
    for x in range(length):
        c = source[x]
        dest[n] = lut[c >> 4]  # current pixel
        n += 1
        dest[n] = lut[c & 0x0f]  # next pixel
        n += 1

class GC9A01(Graphics):
    # Transpose width & height for landscape mode
    def __init__(self, spi, cs, dc, rst, bl, height=240, width=240, inverse=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self._bl = PWM(bl,duty=0)
        self.height = height
        self.width = width
        mode = framebuf.GS4_HMSB
        self._lut = COLOR_LUT
        gc.collect()
        buf = bytearray(self.height * self.width // 2)
        self._mvb = memoryview(buf)
        super().__init__(buf, self.width, self.height, mode)
        linebuf = bytearray(self.width * 2)
        self._mvl = memoryview(linebuf)
        # Hardware reset
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(100)
        self._wcmd(b"\x11")  # SLPOUT
        sleep_ms(50)
        self._wcmd(b"\xFE")
        self._wcmd(b"\xEF")
        self._wcd(b"\xEB",b"\x14")
        self._wcd(b"\x84",b"\x40")
        self._wcd(b"\x85",b"\xF1")
        self._wcd(b"\x86",b"\x98")
        self._wcd(b"\x87",b"\x28")
        self._wcd(b"\x88",b"\x0A")
        self._wcd(b"\x8A",b"\x00")
        self._wcd(b"\x8B",b"\x80")
        self._wcd(b"\x8C",b"\x01")
        self._wcd(b"\x8D",b"\x00")
        self._wcd(b"\x8E",b"\xDF")
        self._wcd(b"\x8F",b"\x52")
        self._wcd(b"\xB6",b"\x20")
        self._wcd(b"\x36",b"\x48")
        self._wcd(b"\x3A",b"\x05")
        self._wcd(b"\x90",b"\x08\x08\x08\x08")
        self._wcd(b"\xBD",b"\x06")
        self._wcd(b"\xA6",b"\x74")
        self._wcd(b"\xBF",b"\x1C")
        self._wcd(b"\xA7",b"\x45")
        self._wcd(b"\xA9",b"\xBB")
        self._wcd(b"\xB8",b"\x63")
        self._wcd(b"\xBC",b"\x00")
        self._wcd(b"\xFF",b"\x60\x01\x04")
        self._wcd(b"\xC3",b"\x17")
        self._wcd(b"\xC4",b"\x17")
        self._wcd(b"\xC9",b"\x25")
        self._wcd(b"\xBE",b"\x11")
        self._wcd(b"\xE1",b"\x10\x0E")
        self._wcd(b"\xDF",b"\x21\x10\x02")
        self._wcd(b"\xF0",b"\x45\x09\x08\x08\x26\x2A")
        self._wcd(b"\xF1",b"\x43\x70\x72\x36\x37\x6F")
        self._wcd(b"\xF2",b"\x45\x09\x08\x08\x26\x2A")
        self._wcd(b"\xF3",b"\x43\x70\x72\x36\x37\x6F")
        self._wcd(b"\xED",b"\x1B\x0B")
        self._wcd(b"\xAC",b"\x47")
        self._wcd(b"\xAE",b"\x77")
        self._wcd(b"\xCB",b"\x02")
        self._wcd(b"\xCD",b"\x63")
        self._wcd(b"\x70",b"\x07\x09\x04\x0E\x0F\x09\x07\x08\x03")
        self._wcd(b"\xE8",b"\x34")
        self._wcd(b"\x62",b"\x18\x0D\x71\xED\x70\x70\x18\x0F\x71\xEF\x70\x70")
        self._wcd(b"\x63",b"\x18\x11\x71\xF1\x70\x70\x18\x13\x71\xF3\x70\x70")
        self._wcd(b"\x64",b"\x28\x29\x01\xF1\x00\x07\xF1")
        self._wcd(b"\x66",b"\x3C\x00\xCD\x67\x45\x45\x10\x00\x00\x00")
        self._wcd(b"\x67",b"\x00\x3C\x00\x00\x00\x01\x54\x10\x32\x98")
        self._wcd(b"\x74",b"\x10\x80\x80\x00\x00\x4E\x00")
        self._wcd(b"\x35",b"\x00")  
        self._wcmd(b"\x20" if inverse else b"\x21") 
        # TFT_NORON: Set Normal display on", no args", w/delay: 10 ms delay
        self._wcmd(b"\x13")
        # TFT_DISPON: Set Main screen turn on", no args w/delay: 100 ms delay
        self._wcmd(b"\x29")
        
            
    # Write a command.
    def _wcmd(self, buf):
        self._dc(0)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    # Write a command followed by a data arg.
    def _wcd(self, command, data):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def sleep(self):
        self._wcmd(b"\x10")

    def wake(self):
        self._wcmd(b"\x11")

    @micropython.native
    def show(self, modonly=True):
        xs, xe, ys, ye = self.getMod()
        if xe < xs:
            return
        xs = xs & 0xFFFE  
        xe = xe | 1
        clut = self._lut
        wd = self.width // 2
        wdc = (xe-xs)//2 + 1
        lb =  self._mvl
        buf = self._mvb
        self._wcd(b"\x2a", int.to_bytes((xs << 16) + xe, 4, "big")) # SET_COLUMN
        self._wcd(b"\x2b", int.to_bytes((ys << 16) + ye, 4, "big"))
        self._wcmd(b"\x2c")  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        for i in range(ys, ye + 1):
            st = i * wd
            _lcopy(lb, buf[st + xs//2 :], clut, wdc)  # Copy and map colors
            self._spi.write(lb[0:wdc*4])
        self._cs(1)
        self.clearMod()

    def bright(self,v):
        v = int(v * 1023)
        v = 1023 if v > 1023 else 0 if v < 0 else v
        self._bl.duty(v)
