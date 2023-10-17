# adapted from https://pyokagan.name/blog/2019-10-14-png/

from tempos import g
from graphics import rgb, BLACK
import deflate
import struct
import micropython
from time import ticks_ms, ticks_diff
try:
    import io
except ImportError:
    import uio as io
from config import TILE_FILE

SHIFT = 40 if g.width>240 else 0

def decompress(data):
    f = io.BytesIO(data)
    with deflate.DeflateIO(f, deflate.ZLIB,15) as g:
        return g.read()

@micropython.viper
def init_plte(plte, palette):
    po = ptr8(plte)
    pal = ptr8(palette)
    for i in range(256):
        col = int(rgb(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]))
        po[i * 2 + 1] = col >> 8
        plte[i * 2] = col

class PNG_Tile:
    def __init__(self, tilex, tiley, zoom, stx, sty):
        self._stx = stx
        self._sty = sty
        self._tile = (tilex, tiley, zoom)
        self._data = None
        self._plte = bytearray(512)
        self._decode()
        self._row = 0
        self._col = 0
        self._x = 0
        self._y = 0

    @micropython.viper
    def _init_plte(self, palette):
        po = ptr8(self._plte)
        pal = ptr8(palette)
        for i in range(256):
            col = int(rgb(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]))
            po[i * 2 + 1] = col >> 8
            po[i * 2] = col

    def _decode(self):
        def read_chunk(f):
            # Returns (chunk_type, chunk_data)
            chunk_length, chunk_type = struct.unpack(">I4s", f.read(8))
            chunk_data = f.read(chunk_length)
            (chunk_expected_crc,) = struct.unpack(">I", f.read(4))
            return chunk_type, chunk_data
        # now = ticks_ms()
        # open file and check signature
        try:
            f = open(
                "/sd/{}/{}/{}/{}.png".format(
                    TILE_FILE, self._tile[2], self._tile[0], self._tile[1]
                ),
                "rb",
            )
        except:
            return
        PngSignature = b"\x89PNG\r\n\x1a\n"
        if f.read(len(PngSignature)) != PngSignature:
            raise Exception(
                "Invalid PNG Signature {}/{}/{}.png".format(
                    self._tile[2], self._tile[0], self._tile[1]
                )
            )
        chunks = []
        while True:
            chunk_type, chunk_data = read_chunk(f)
            chunks.append((chunk_type, chunk_data))
            if chunk_type == b"IEND":
                break
        _, IHDR_data = chunks[0]  # IHDR is always first chunk
        width, height, bitd, colort, compm, filterm, interlacem = struct.unpack(
            ">IIBBBBB", IHDR_data
        )
        if not (width == 256 and height == 256):
            raise Exception("only 256x256 images")
        if compm != 0:
            raise Exception("invalid compression method")
        if filterm != 0:
            raise Exception("invalid filter method")
        if colort != 3:
            raise Exception("only paletted color for OSM map tiles")
        if bitd != 1 and bitd != 8:
            raise Exception("only bit depth of 1 or 8")
        if interlacem != 0:
            raise Exception("no interlacing support")
        if bitd == 8:
            data = b""
            for chunk_type, chunk_data in chunks:
                if chunk_type == b"PLTE":
                    # get image data
                    self._plte = bytearray(512)
                    self._init_plte(chunk_data)
                elif chunk_type == b"IDAT":
                    # get image data
                    data = data+chunk_data;
            self._data = decompress(data)
        else:
            chunk_type, palette = chunks[1]
            if not chunk_type == b"PLTE":
                raise Exception("Palette chunk expected")
            self._plte = rgb(palette[0], palette[1], palette[2])
            self._data = b"\x00"
        # print("Decode Time(ms): ",ticks_diff(ticks_ms(),now))

    @micropython.viper
    def _render(self, w: int, h: int):
        baddr = ptr8(g._buf)
        bwidth = 2 * int(g.width)
        dt = ptr8(self._data)
        pal = ptr8(self._plte)
        rs = int(self._row)
        cs = int(self._col)
        xs = int(self._x) + int(SHIFT)
        ys = int(self._y)
        for j in range(0, h):
            for i in range(0, w):
                col = dt[(rs + j) * 257 + i + cs + 1]
                ind: int = (j + ys) * bwidth + (xs + i) * 2
                baddr[ind] = pal[col * 2]
                baddr[ind + 1] = pal[col * 2 + 1]

    def _clip(self, w, h):
        if self._col + w > 256:
            w = 256 - self._col
        if self._x + w > 240:
            w = 240 - self._x
        if self._row + h > 256:
            h = 256 - self._row
        if self._y + h > 240:
            h = 240 - self._y
        return w, h

    def draw(self, c, r, x, y, w, h):
        self._row = r
        self._col = c
        self._x = x
        self._y = y
        w, h = self._clip(w, h)
        # now = ticks_ms()
        if self._data is not None:
            if len(self._data) > 1:
                self._render(w, h)
                g.updateMod(x, y, x + w - 1, y + h - 1)
            else:
                g.fill_rect(x+SHIFT, y, w, h, self._plte)
        else:
            g.fill_rect(x+SHIFT, y, w, h, BLACK)
        # print("Draw Time(ms): ",ticks_diff(ticks_ms(),now))

    def draw_chunk(self, x1, y1, x2, y2):  # coords in 0..511,0..511 space
        def in_tile(x, y):
            return (
                x >= self._stx
                and x < self._stx + 256
                and y >= self._sty
                and y < self._sty + 256
            )

        if in_tile(x1, y1):
            self.draw(
                x1 - self._stx, y1 - self._sty, 0, 0, 240, 240
            )  # rely on clipping
        elif in_tile(x2, y1):
            self.draw(0, y1 - self._sty, 256 - x1, 0, 240, 240)
        elif in_tile(x1, y2):
            self.draw(x1 - self._stx, 0, 0, 256 - y1, 240, 240)
        elif in_tile(x2, y2):
            self.draw(0, 0, 256 - x1, 256 - y1, 240, 240)
