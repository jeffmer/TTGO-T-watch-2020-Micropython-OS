import  math, framebuf, gc
from graphics import Graphics
from time import sleep_ms, ticks_ms, ticks_diff
from graphics import Graphics


@micropython.viper
def _map(src:ptr8, dest:ptr8,xs:int,xe:int,ys:int,ye:int,width:int):
    for x in range(xs,xe+1):
        for y in range(ys,ye+1):
            row = x//2
            col = y//12
            bit = (1+((11 - y%12)<<1)) if x%2 ==0 else (11 - y%12)<<1
            index = 3*(col*width//2 + row)+(2-bit//8)
            v = src[(y//8)*width+x] & (1<<y%8)
            if v!=0:
                dest[index] |= 1<<(bit%8) 
            else:
                dest[index] &= 255-(1<<(bit%8))


class ST7302(Graphics):
    def __init__(self, spi, cs, dc, rst, height=122, width=250, inverse=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.height = height
        self.width = width
        mode = framebuf.MONO_VLSB
        gc.collect()
        self.buf = bytearray(math.ceil(height/8)*width)
        self._mvb = memoryview(self.buf)
        super().__init__(self.buf, self.width, self.height, mode)
        self.screenbuf = bytearray(3*math.ceil(height/12)*width//2)
        self._screen = memoryview(self.screenbuf)
        # Hardware reset
        self._rst(0)
        sleep_ms(100)
        self._rst(1)
        sleep_ms(150)
        self._wcd(b"\xeb",b"\x02") # Enable OTP
        self._wcd(b"\xd7",b"\68")  # OTP Load Controlxs, xe, ys, ye,
        self._wcd(b"\xEB",b"\x02")# Enable NVM
        self._wcd(b"\xD7",b"\x68")# NVM Load Control
        self._wcd(b"\xD1",b"\x01")# Booster enable
        self._wcd(b"\xC0",b"\x80") # Gate Voltage Setting VGH=12V; VGL=-5V
        self._wcd(b"\xC1",b"\x28\x28\x28\x28\x14\x00")  # Source Voltage Control 1
        self._wcmd(b"\xC2")      # Source Voltage Control 2
        self._wcd(b"\xCB",b"\x14") # VCOMH Voltage Setting 4V
        self._wcd(b"\xB4",b"\xE5\x77\xF1\xFF\xFF\x4F\xF1\xFF\xFF\x4F")
        self._wcd(b"\xB2",b"\x01\x04") # frame rate 32Hz high power 4 Hz low power
        self._wcmd(b"\x11")        # sleep out
        sleep_ms(100)
        self._wcd("b\xC7","b\xA6\xE9") # OSC Enable
        self._wcd(b"\x36",b"\x20") # Memory Data Access Control
        self._wcd(b"\xD0",b"\x1F") # Unknown command??
        self._wcd(b"\x3a",b"\x11") # DataFormatSelect4writefor24bit
        self._wcd(b"\xb0",b"\x64") # Duty setting 250duty/4=63
        self._wcd(b"\xb8",b"\x09") # Panel Setting Frame inversion
        self._wcmd(b"\x29")        # Display on
        self._wcd(b"\xB9",b"\0xE3")  # Clear RAM
        sleep_ms(100)
        self._wcd(b"\xB9",b"\x23")  # Source Setting Off
        self._wcmd(b"\x39")         # Low Power
        sleep_ms(100)

      
    # Write a command.
    def _wcmd(self, buf):
        self._cs(0)
        self._dc(0)
        self._spi.write(buf)
        self._cs(1)

    # Write a command followed by a data arg.
    def _wcd(self, command, data):
        self._cs(0)
        self._dc(0)
        self._spi.write(command)
        self._dc(1)
        self._spi.write(data)
        self._cs(1)
        
    def _wcd2(self,command,v1,v2):
        tmp = bytearray(2)
        tmp[0]=v1
        tmp[1]=v2
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._dc(1)
        self._spi.write(tmp)
        self._cs(1)

    def sleep(self):
        self._wcmd(b"\x10")

    def wake(self):
        self._wcmd(b"\x11")
        
    def invert(self,v):
        self._wcmd(b"\x21" if v else b"\x20")
        sleep_ms(100)
        
    @micropython.native
    def show(self, modonly=True):
        start = ticks_ms()
        xs, xe, ys, ye = self.getMod()
        if xe < xs:
            return
        _map(self._mvb, self._screen, xs, xe, ys, ye, self.width)      
        self._wcd2(b"\x2a",25,35) 
        self._wcd2(b"\x2b",0,124)
        self._wcmd(b"\x2c")  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        self._spi.write(self._screen)
        self._cs(1)
        self.clearMod()
        print("Show ",ticks_diff(ticks_ms(),start),"ms")

