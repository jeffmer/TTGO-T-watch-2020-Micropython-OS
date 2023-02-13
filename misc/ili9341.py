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
    def __init__(self, spi, cs, dc, rst, height=240, width=320,
                 usd=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.height = height
        self.width = width
        mode = framebuf.RGB565
        gc.collect()
        self.buf = bytearray(self.height * self.width * 2)
        super().__init__(self.buf, self.width, self.height, mode)
        # Hardware reset
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(50)
        # Send initialization commands
        self._wcmd(b'\x01')  # SWRESET Software reset
        sleep_ms(100)
        self._wcd(b'\xcf', b'\x00\xC1\x30')  # PWCTRB Pwr ctrl B
        self._wcd(b'\xed', b'\x64\x03\x12\x81')  # POSC Pwr on seq. ctrl
        self._wcd(b'\xe8', b'\x85\x00\x78')  # DTCA Driver timing ctrl A
        self._wcd(b'\xcb', b'\x39\x2C\x00\x34\x02')  # PWCTRA Pwr ctrl A
        self._wcd(b'\xf7', b'\x20')  # PUMPRC Pump ratio control
        self._wcd(b'\xea', b'\x00\x00')  # DTCB Driver timing ctrl B
        self._wcd(b'\xc0', b'\x23')  # PWCTR1 Pwr ctrl 1
        self._wcd(b'\xc1', b'\x10')  # PWCTR2 Pwr ctrl 2
        self._wcd(b'\xc5', b'\x3E\x28')  # VMCTR1 VCOM ctrl 1
        self._wcd(b'\xc7', b'\x86')  # VMCTR2 VCOM ctrl 2
        # (b'\x88', b'\xe8', b'\x48', b'\x28')[rotation // 90]
        if self.height > self.width:
            self._wcd(b'\x36', b'\x48' if usd else b'\x88')  # MADCTL: RGB portrait mode
        else:
            self._wcd(b'\x36', b'\x28' if usd else b'\xe8')  # MADCTL: RGB landscape mode
        self._wcd(b'\x37', b'\x00')  # VSCRSADD Vertical scrolling start address
        self._wcd(b'\x3a', b'\x55')  # PIXFMT COLMOD: Pixel format 16 bits (MCU & interface)
        self._wcd(b'\xb1', b'\x00\x18')  # FRMCTR1 Frame rate ctrl
        self._wcd(b'\xb6', b'\x08\x82\x27')  # DFUNCTR
        self._wcd(b'\xf2', b'\x00')  # ENABLE3G Enable 3 gamma ctrl
        self._wcd(b'\x26', b'\x01')  # GAMMASET Gamma curve selected
        self._wcd(b'\xe0', b'\x0F\x31\x2B\x0C\x0E\x08\x4E\xF1\x37\x07\x10\x03\x0E\x09\x00')  # GMCTRP1
        self._wcd(b'\xe1', b'\x00\x0E\x14\x03\x11\x07\x31\xC1\x48\x08\x0F\x0C\x31\x36\x0F')  # GMCTRN1
        self._wcmd(b'\x11')  # SLPOUT Exit sleep
        sleep_ms(100)
        self._wcmd(b'\x29')  # DISPLAY_ON
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
        
# Time (ESP32 240MHz freq) 32ms landscape.
# @micropython.native - makes no difference
    def show(self,modonly=True):
        xs,xe,ys,ye = self.getMod()
        if not modonly or (ye-ys)>(self.height//4):
            self._wcd(b'\x2a', int.to_bytes(self.width-1, 4, 'big'))  # SET_COLUMN
            self._wcd(b'\x2b', int.to_bytes(self.height-1, 4, 'big'))  # SET_PAGE
            self._wcmd(b'\x2c')  # WRITE_RAM
            self._dc(1)
            self._cs(0)
            self._spi.write(self.buf)
            self._cs(1)
        else:
            if xe<xs:
                return
            self._wcd(b'\x2a', int.to_bytes((xs << 16) + xe, 4, 'big'))
            self._wcd(b'\x2b', int.to_bytes((ys << 16) + ye, 4, 'big'))
            self._wcmd(b'\x2c')  # WRITE_RAM
            for i in range(ys,ye+1):
                st = i*self.width*2;
                chunk = memoryview(self.buf[(st+xs*2):(st+xe*2+2)])
                self._dc(1)
                self._cs(0)
                self._spi.write(chunk)
                self._cs(1)
        self.clearMod()


            
