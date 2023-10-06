# ILI9341 nano-gui driver for ili9341 displays
# As with all nano-gui displays, touch is not supported.

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

# This work is based on the following sources.
# https://github.com/rdagger/micropython-ili9341
# Also this forum thread with ideas from @minyiky:
# https://forum.micropython.org/viewtopic.php?f=18&t=9368

from time import sleep_ms
import gc
import framebuf
import graphics


class ILI9341(graphics.Graphics):
    # Transpose width & height for landscape mode
    def __init__(self, spi, cs, dc, bl,height=240, width=320, inverse=True):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self.bright = bl
        self.height = height
        self.width = width
        mode = framebuf.RGB565
        gc.collect()
        self.buf = bytearray(self.height * self.width * 2)
        super().__init__(self.buf, self.width, self.height, mode)
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

    # Time (ESP32 240MHz freq) 32ms landscape.
    # @micropython.native - makes no difference
    def show(self, modonly=True):
        xs, xe, ys, ye = self.getMod()
        if not modonly or (ye - ys) > (self.height // 4):
            self._wcd(b"\x2a", int.to_bytes(self.width - 1, 4, "big"))  # SET_COLUMN
            self._wcd(b"\x2b", int.to_bytes(self.height - 1, 4, "big"))  # SET_PAGE
            self._wcmd(b"\x2c")  # WRITE_RAM
            self._dc(1)
            self._cs(0)
            self._spi.write(self.buf)
            self._cs(1)
        else:
            if xe < xs:
                return
            self._wcd(b"\x2a", int.to_bytes((xs << 16) + xe, 4, "big"))
            self._wcd(b"\x2b", int.to_bytes((ys << 16) + ye, 4, "big"))
            self._wcmd(b"\x2c")  # WRITE_RAM
            for i in range(ys, ye + 1):
                st = i * self.width * 2
                chunk = memoryview(self.buf[(st + xs * 2) : (st + xe * 2 + 2)])
                self._dc(1)
                self._cs(0)
                self._spi.write(chunk)
                self._cs(1)
        self.clearMod()
        

