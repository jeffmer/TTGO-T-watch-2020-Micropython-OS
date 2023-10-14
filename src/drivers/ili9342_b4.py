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

class ILI9341(Graphics):
    # Transpose width & height for landscape mode
    def __init__(self, spi, cs, dc, rst, bl, height=240, width=320, inverse=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self._bl = PWM(bl)
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
        sleep_ms(50)
        self._wcmd(b"\x01")  # SWRESET Software reset
        sleep_ms(100)
        self._wcd(b"\x36", b"\x08")
        self._wcd(b"\x37", b"\x00")  # VSCRSADD Vertical scrolling start address
        self._wcd(b"\x3a", b"\x55")  # PIXFMT COLMOD: Pixel format 16 bits (MCU & interface)
        self._wcd(b"\x26", b"\x08 ")  # GAMMASET Gamma curve selected
        self._wcmd(b"\x21" if inverse else b"\x20") 
        self._wcmd(b"\x11")  # SLPOUT Exit sleep
        sleep_ms(100)
        self._wcmd(b"\x29")  # DISPLAY_ON
        sleep_ms(100)

        
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
