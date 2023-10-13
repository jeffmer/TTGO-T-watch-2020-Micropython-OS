import framebuf
import micropython
from fonts import glcdfont
import math
from config import COLOR_BITS


@micropython.viper
def rgb(r: int, g: int, b: int) -> int:
    """Convert r, g, b in range 0-255 to a 16 bit colour value
    LS byte goes into LUT offset 0, MS byte into offset 1
    Same mapping in linebuf so LS byte is shifted out 1st
    ILI9341 expects RGB order"""
    return (r & 0xF8) | (g & 0xE0) >> 5 | (g & 0x1C) << 11 | (b & 0xF8) << 5

def makecolor(lut,index,r,g,b):
    c = rgb(r, g, b)
    if not 0 <= index <= 15:
        raise ValueError('Colour number must be 0..15')
    lut[index*2] = c & 0xff
    lut[index*2 + 1] = c >> 8
    return index

if COLOR_BITS ==16:
    BLACK = rgb(0, 0, 0)
    GREEN = rgb(0, 255, 0)
    RED = rgb(255, 0, 0)
    LIGHTRED = rgb(140, 0, 0)
    BLUE = rgb(0, 0, 255)
    YELLOW = rgb(255, 255, 0)
    GREY = rgb(100, 100, 100)
    LIGHTGREY = rgb(200, 200, 200)
    MAGENTA = rgb(255, 0, 255)
    CYAN = rgb(0, 255, 255)
    LIGHTGREEN = rgb(0, 100, 0)
    DARKGREEN = rgb(0, 80, 0)
    DARKBLUE = rgb(0, 0, 90)
    WHITE = rgb(255, 255, 255)
else:
    COLOR_LUT = bytearray(32)
    BLACK = makecolor(COLOR_LUT, 0, 0, 0, 0)
    GREEN = makecolor(COLOR_LUT, 1, 0, 255, 0)
    RED = makecolor(COLOR_LUT, 2, 255, 0, 0)
    LIGHTRED = makecolor(COLOR_LUT, 3, 140, 0, 0)
    BLUE = makecolor(COLOR_LUT, 4, 0, 0, 255)
    YELLOW = makecolor(COLOR_LUT, 5, 255, 255, 0)
    GREY = makecolor(COLOR_LUT, 6, 100, 100, 100)
    LIGHTGREY = makecolor(COLOR_LUT, 7, 200, 200, 200)
    MAGENTA = makecolor(COLOR_LUT, 8, 255, 0, 255)
    CYAN = makecolor(COLOR_LUT, 9, 0, 255, 255)
    LIGHTGREEN = makecolor(COLOR_LUT, 10, 0, 100, 0)
    DARKGREEN = makecolor(COLOR_LUT, 11, 0, 80, 0)
    DARKBLUE = makecolor(COLOR_LUT, 12, 0, 0, 90)
    WHITE = makecolor(COLOR_LUT, 15, 255, 255, 255)



def rotate(coord, theta):
    "rotates an integer array of coordinates by angle theta"
    sinr = math.sin(theta)
    cosr = math.cos(theta)
    for i in range(0, len(coord), 2):
        x, y = coord[i], coord[i + 1]
        coord[i] = math.ceil(x * cosr - y * sinr)
        coord[i + 1] = math.ceil(x * sinr + y * cosr)
    return coord


class BoolPalette(framebuf.FrameBuffer):
    def __init__(self, mode):
        buf = bytearray(4)  # OK for <= 16 bit color
        super().__init__(buf, 2, 1, mode)

    def fg(self, color):  # Set foreground color
        self.pixel(1, 0, color)

    def bg(self, color):
        self.pixel(0, 0, color)


class Graphics(framebuf.FrameBuffer):
    def __init__(self, buf, w, h, mode):
        self.minX = 9999
        self.maxX = -9999
        self.minY = 9999
        self.maxY = -9999
        self.width = w
        self.height = h
        self._font = glcdfont
        self._align = (-1, -1)  # top left
        self.palette = BoolPalette(mode)
        self.fgcolor = WHITE
        self.bgcolor = BLACK
        self._buf = buf
        super().__init__(buf, w, h, mode)

    def updateMod(self, x1: int, y1: int, x2: int, y2: int):
        self.minX = x1 if x1 < self.minX and x1 >= 0 else self.minX
        self.maxX = x2 if x2 > self.maxX and x2 < self.width else self.maxX
        self.minY = y1 if y1 < self.minY and y1 >= 0 else self.minY
        self.maxY = y2 if y2 > self.maxY and y2 < self.height else self.maxY

    def getMod(self):
        return self.minX, self.maxX, self.minY, self.maxY

    def clearMod(self):
        self.minX = 9999
        self.maxX = -9999
        self.minY = 9999
        self.maxY = -9999
        self._align = (-1, -1)

    def fill(self, c):
        self.updateMod(0, 0, self.width - 1, self.height - 1)
        super().fill(c)

    def draw_pixel(self, x, y, c=None):
        self.updateMod(x, y, x, y)
        super().pixel(x, y, c if c is not None else self.fgcolor)

    def hline(self, x, y, w, c=None):
        self.updateMod(x, y, x + w - 1, y)
        super().hline(x, y, w, c if c is not None else self.fgcolor)

    def vline(self, x, y, h, c=None):
        self.updateMod(x, y, x, y + h - 1)
        super().vline(x, y, h, c if c is not None else self.fgcolor)

    def line(self, x1, y1, x2, y2, c=None):
        self.updateMod(x1, y1, x1, y1)
        self.updateMod(x2, y2, x2, y2)
        super().line(x1, y1, x2, y2, c if c is not None else self.fgcolor)

    def rect(self, x, y, w, h, c=None):
        self.updateMod(x, y, x + w - 1, y + h - 1)
        super().rect(x, y, w, h, c if c is not None else self.fgcolor)

    def fill_rect(self, x, y, w, h, c=None):
        self.updateMod(x, y, x + w - 1, y + h - 1)
        super().fill_rect(x, y, w, h, c if c is not None else self.fgcolor)

    def ellipse(self, x, y, xr, yr, c=None, f=False, m=15):
        self.updateMod(x - xr, y - yr, x + xr, y + yr)
        super().ellipse(x, y, xr, yr, c if c is not None else self.fgcolor, f, m)

    def poly(self, x, y, coord, c=None, f=False, theta=None):
        if theta is not None:
            coord = rotate(coord, theta)
        for i in range(0, len(coord), 2):
            x1, y1 = x + coord[i], y + coord[i + 1]
            self.updateMod(x1, y1, x1, y1)
        super().poly(x, y, coord, c if c is not None else self.fgcolor, f)

    def setfont(self, font):
        self._font = font

    def getfont(self):
        return self._font

    def setcolor(self, fgcolor=None, bgcolor=None):
        if fgcolor is not None:
            self.fgcolor = fgcolor
        if bgcolor is not None:
            self.bgcolor = bgcolor
        return self.fgcolor, self.bgcolor

    def setfontalign(self, xalign, yalign):
        self._align = (xalign, yalign)

    def text_dim(self, str):
        return self._font.get_width(str), self._font.height()

    def text(self, str, x, y, c=None):
        "write a string of text. Optional color of letters can be specified by c"
        str_w, str_h = self.text_dim(str)
        x_a, y_a = self._align
        x = x if x_a == -1 else x - str_w if x_a == 1 else x - str_w // 2
        y = y if y_a == -1 else y - str_h if y_a == 1 else y - str_h // 2
        div, rem = divmod(str_h, 8)
        nbytes = div + 1 if rem else div
        buf = bytearray(str_w * nbytes)
        pos = 0
        for ch in str:
            glyph, char_w = self._font.get_ch(ch)
            for row in range(nbytes):
                index = row * str_w + pos
                for i in range(char_w):
                    buf[index + i] = glyph[nbytes * i + row]
            pos += char_w
        fb = framebuf.FrameBuffer(buf, str_w, str_h, framebuf.MONO_VLSB)
        palette = self.palette
        palette.bg(self.bgcolor)
        palette.fg(c if c is not None else self.fgcolor)
        self.blit(fb, x, y, self.bgcolor, palette)  # make background transparent
        self.updateMod(x, y, x + str_w - 1, y + str_h - 1)
        return str_w

    def wordwraptext(self, str, x, y, w, c=None):
        "write a string of text of color c. Automatically wrap text if the width is larger than w"
        curx = x
        cury = y
        char_h = self._font.height()
        char_w = self._font.max_width()
        lines = str.split("\n")
        for line in lines:
            words = line.split(" ")
            for word in words:
                ww = self._font.get_width(word)
                if curx + ww >= w:
                    curx = x
                    cury += char_h
                    while ww > w:
                        self.text(word[: w // char_w], curx, cury, c)
                        word = word[w // char_w :]
                        cury += char_h
                if len(word) > 0:
                    curx += self.text(word + " ", curx, cury, c)
            curx = x
            cury += char_h

    def screendump(self, name):
        with open(name + ".raw", "wb") as f:
            f.write(bytes(self._buf))
            f.close()
