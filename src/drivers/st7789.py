# ILI9341 nano-gui driver for ili9341 displays
# As with all nano-gui displays, touch is not supported.

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

# This work is based on the following sources.
# https://github.com/rdagger/micropython-ili9341
# Also this forum thread with ideas from @minyiky:
# https://forum.micropython.org/viewtopic.php?f=18&t=9368
from micropython import const
from machine import PWM
from time import sleep_ms
import gc
import framebuf
import graphics
XOFF = const(0)
YOFF = const(80)
INVERSE = const(1)

class ST7789(graphics.Graphics):

    # Transpose width & height for landscape mode
    def __init__(self, spi, cs, dc, bl, rst=None, height=240, width=240,
                 usd=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._bl = PWM(bl)
        self._bl.freq(1000)
        self._rst = rst
        self.height = height
        self.width = width
        mode = framebuf.RGB565
        gc.collect()
        self.buf = bytearray(self.height * self.width * 2)
        super().__init__(self.buf, self.width, self.height, mode)
        if not rst is None:
            self._rst(0)
            sleep_ms(10)
            self._rst(1)
        else:
            self._wcmd(b'\x01')  # SWRESET Software reset
        sleep_ms(120)
        self._wcmd(b'\x11') # SLPOUT
        sleep_ms(50)
        #MADCTL: Set Memory access control (directions), 1 arg: row addr/col addr, bottom to top refresh
        self._wcd(b'\x36', b'\x08')
        #COLMOD: Set color mode, 1 arg, no delay: 16-bit color
        self._wcd(b'\x3a', b'\x05')
        #PORCTRL: Porch control
        self._wcd(b'\xb2', b'\x0c\x0c\x00\x33\x33')
        #GCTRL: Gate control
        self._wcd(b'\xb7', b'\x00')
        # VCOMS: VCOMS setting
        self._wcd(b'\xbb', b'\x3e')
        #LCMCTRL: CM control
        self._wcd(b'\xc0', b'\xc0')
        #VDVVRHEN: VDV and VRH command enable
        self._wcd(b'\xc2', b'\x01')
        # VRHS: VRH Set
        self._wcd(b'\xc3', b'\x19')
        # VDVS: VDV Set
        self._wcd(b'\xc4', b'\x20')
        #VCMOFSET: VCOM Offset Set .
        self._wcd(b'\xC5', b'\x0F')
        #PWCTRL1: Power Control 1
        self._wcd(b'\xD0', b'\xA4\xA1')
        # PVGAMCTRL: Positive Voltage Gamma Control
        self._wcd(b'\xe0', b'\x70\x15\x20\x15\x10\x09\x48\x33\x53\x0B\x19\x15\x2a\x2f')
        #self._wcd(b'\xe0', b'\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17')
        # NVGAMCTRL: Negative Voltage Gamma Contro
        self._wcd(b'\xe1', b'\x70\x15\x20\x15\x10\x09\x48\x33\x53\x0B\x19\x15\x2a\x2f')
        #self._wcd(b'\xe0', b'\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e')
        if INVERSE:
            #TFT_INVONN: Invert display, no args, no delay
            self._wcmd(b'\x21')
        else:
            #TFT_INVOFF: Don't invert display, no args, no delay
            self._wcmd(b'\x20')
        #TFT_NORON: Set Normal display on, no args, w/delay: 10 ms delay
        self._wcmd(b'\x13');
        #TFT_DISPON: Set Main screen turn on, no args w/delay: 100 ms delay
        self._wcmd(b'\x29');
        
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
        self._wcmd(b'\x10')

    def wake(self):
        self._wcmd(b'\x11')

        
# Time (ESP32 240MHz freq) 32ms landscape.
# @micropython.native - makes no difference
    def show(self,modonly=True):
        xs,xe,ys,ye = self.getMod()
        if not modonly or (ye-ys)>(self.height//2):
            self._wcd(b'\x2a', int.to_bytes(self.width+XOFF-1 + (XOFF << 16), 4, 'big'))  # SET_COLUMN
            self._wcd(b'\x2b', int.to_bytes(self.height+YOFF-1 + (YOFF << 16), 4, 'big'))  # SET_PAGE
            self._wcmd(b'\x2c')  # WRITE_RAM
            self._dc(1)
            self._cs(0)
            self._spi.write(self.buf)
            self._cs(1)
        else:
            if xe<xs or ye<ys:
                return
            self._wcd(b'\x2a', int.to_bytes(((xs+XOFF) << 16) + xe + XOFF, 4, 'big'))
            self._wcd(b'\x2b', int.to_bytes(((ys+YOFF) << 16) + ye + YOFF, 4, 'big'))
            self._wcmd(b'\x2c')  # WRITE_RAM
            for i in range(ys,ye+1):
                st = i*self.width*2;
                chunk = memoryview(self.buf[(st+xs*2):(st+xe*2+2)])
                self._dc(1)
                self._cs(0)
                self._spi.write(chunk)
                self._cs(1)
        self.clearMod()

    # screen brightness function
    def bright(self,v):
        v = int(v*1023)
        v = 1023 if v>1023 else 0 if v<0 else v
        self._bl.duty(v);


