# png.py - PNG encoder/decoder in pure Python
#
# Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
# Portions Copyright (C) 2009 David Jones <drj@pobox.com>
# And probably portions Copyright (C) 2006 Nicko van Someren <nicko@nicko.org>
# Micropython port Copyright (C) 2016 Clayton G. Hobbs
#
# Original concept by Johann C. Rocholl.
#
# LICENCE (MIT)
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

try:
    import io
except ImportError:
    import uio as io
import itertools
import math
import deflate

# import re
try:
    import struct
except ImportError:
    import ustruct as struct
# import warnings


from array import array

from tempos import g
from graphics import rgb
import framebuf
import machine

# from functools import reduce


# __all__ = ['Image', 'Reader', 'Writer', 'write_chunks', 'from_array']
# __all__ = ['Reader']


# The PNG signature.
# http://www.w3.org/TR/PNG/#5PNG-file-signature
_signature = struct.pack("8B", 137, 80, 78, 71, 13, 10, 26, 10)

_adam7 = (
    bytearray((0, 0, 8, 8)),
    bytearray((4, 0, 8, 8)),
    bytearray((0, 4, 4, 8)),
    bytearray((2, 0, 4, 4)),
    bytearray((0, 2, 2, 4)),
    bytearray((1, 0, 2, 2)),
    bytearray((0, 1, 1, 2)),
)


def group(s, n):
    return list(zip(*[iter(s)] * n))


class Error(Exception):
    def __str__(self):
        return self.__class__.__name__ + ": " + " ".join(self.args)


class FormatError(Error):
    pass


class ChunkError(FormatError):
    pass


def decompress(data):
    f = io.BytesIO(data)
    with deflate.DeflateIO(f, deflate.ZLIB,15) as g:
        return g.read()

class Reader:
    """
    PNG decoder in pure Python.
    """

    def __init__(self, **kw):
        """
        Create a PNG decoder object.

        The constructor expects exactly one keyword argument.  You can
        choose among the following keyword arguments:

        filename
          Name of input file (a PNG file).
        file
          A file-like object (object with a read() method).
        bytes
          ``array`` or ``string`` with PNG data.

        """
        if len(kw) != 1:
            raise TypeError("Reader() takes exactly 1 argument")

        # Will be the first 8 bytes, later on.  See validate_signature.
        self.signature = None
        self.transparent = None
        # A pair of (len,type) if a chunk has been read but its data and
        # checksum have not (in other words the file position is just
        # past the 4 bytes that specify the chunk type).  See preamble
        # method for how this is used.
        self.atchunk = None

        if "filename" in kw:
            self.file = open(kw["filename"], "rb")
        elif "file" in kw:
            self.file = kw["file"]
        elif "bytes" in kw:
            self.file = io.BytesIO(kw["bytes"])
        else:
            raise TypeError("expecting filename, file or bytes array")

    def chunk(self, seek=None):
        """
        Read the next PNG chunk from the input file; returns a
        (*type*, *data*) tuple.  *type* is the chunk's type as a
        byte string (all PNG chunk types are 4 bytes long).
        *data* is the chunk's data content, as a byte string.

        If the optional `seek` argument is
        specified then it will keep reading chunks until it either runs
        out of file or finds the type specified by the argument.  Note
        that in general the order of chunks in PNGs is unspecified, so
        using `seek` can cause you to miss chunks.
        """

        self.validate_signature()

        while True:
            # http://www.w3.org/TR/PNG/#5Chunk-layout
            if not self.atchunk:
                self.atchunk = self.chunklentype()
            length, type = self.atchunk
            self.atchunk = None
            data = self.file.read(length)
            if len(data) != length:
                raise ChunkError("EOF reading chunk %s" % type)
            checksum = self.file.read(4)
            if len(checksum) != 4:
                raise ChunkError("EOF reading chunk %s" % type)
            if seek and type != seek:
                continue
            return type, data

    def chunks(self):
        """Return an iterator that will yield each chunk as a
        (*chunktype*, *content*) pair.
        """

        while True:
            t, v = self.chunk()
            yield t, v
            if t == b"IEND":
                break

    def undo_filter(self, filter_type, scanline, previous):
        """Undo the filter for a scanline.  `scanline` is a sequence of
        bytes that does not include the initial filter type byte.
        `previous` is decoded previous scanline (for straightlaced
        images this is the previous pixel row, but for interlaced
        images, it is the previous scanline in the reduced image, which
        in general is not the previous pixel row in the final image).
        When there is no previous scanline (the first row of a
        straightlaced image, or the first row in one of the passes in an
        interlaced image), then this argument should be ``None``.

        The scanline will have the effects of filtering removed, and the
        result will be returned as a fresh sequence of bytes.
        """

        # :todo: Would it be better to update scanline in place?
        # Yes, with the Cython extension making the undo_filter fast,
        # updating scanline inplace makes the code 3 times faster
        # (reading 50 images of 800x800 went from 40s to 16s)
        result = scanline

        if filter_type == 0:
            return result

        if filter_type not in (1, 2, 3, 4):
            raise FormatError("Invalid filter")

        # Filter unit.  The stride from one pixel to the corresponding
        # byte from the previous pixel.  Normally this is the pixel
        # size in bytes, but when this is smaller than 1, the previous
        # byte is used instead.
        fu = max(1, self.psize)

        # For the first line of a pass, synthesize a dummy previous
        # line.  An alternative approach would be to observe that on the
        # first line 'up' is the same as 'null', 'paeth' is the same
        # as 'sub', with only 'average' requiring any special case.
        if not previous:
            previous = array("B", [0] * len(scanline))

        # Call appropriate filter algorithm.  Note that 0 has already
        # been dealt with.
        (
            None,
            pngfilters.undo_filter_sub,
            pngfilters.undo_filter_up,
            pngfilters.undo_filter_average,
            pngfilters.undo_filter_paeth,
        )[filter_type](fu, scanline, previous, result)
        return result

    def deinterlace(self, raw):
        """
        Read raw pixel data, undo filters, deinterlace, and flatten.
        Return in flat row flat pixel format.
        """

        # Values per row (of the target image)
        vpr = self.width * self.planes

        # Make a result array, and make it big enough.  Interleaving
        # writes to the output array randomly (well, not quite), so the
        # entire output array must be in memory.
        a = array("BH"[self.bitdepth > 8], [0] * vpr * self.height)
        source_offset = 0

        for xstart, ystart, xstep, ystep in _adam7:
            if xstart >= self.width:
                continue
            # The previous (reconstructed) scanline.  None at the
            # beginning of a pass to indicate that there is no previous
            # line.
            recon = None
            # Pixels per row (reduced pass image)
            ppr = int(math.ceil((self.width - xstart) / float(xstep)))
            # Row size in bytes for this pass.
            row_size = int(math.ceil(self.psize * ppr))
            for y in range(ystart, self.height, ystep):
                filter_type = raw[source_offset]
                source_offset += 1
                scanline = raw[source_offset : source_offset + row_size]
                source_offset += row_size
                recon = self.undo_filter(filter_type, scanline, recon)
                # Convert so that there is one element per pixel value
                flat = self.serialtoflat(recon, ppr)
                if xstep == 1:
                    assert xstart == 0
                    offset = y * vpr
                    a[offset : offset + vpr] = flat
                else:
                    offset = y * vpr + xstart * self.planes
                    end_offset = (y + 1) * vpr
                    skip = self.planes * xstep
                    for i in range(self.planes):
                        # a[offset+i:end_offset:skip] = \
                        #    flat[i::self.planes]
                        for item, dest in zip(
                            itertools.islice(flat, i, len(flat), self.planes),
                            range(offset + i, end_offset, skip),
                        ):
                            a[dest] = item
        return a

    def iterboxed(self, rows):
        """Iterator that yields each scanline in boxed row flat pixel
        format.  `rows` should be an iterator that yields the bytes of
        each row in turn.
        """

        def asvalues(raw):
            """Convert a row of raw bytes into a flat row.  Result will
            be a freshly allocated object, not shared with
            argument.
            """

            if self.bitdepth == 8:
                return array("B", raw)
            if self.bitdepth == 16:
                raw = bytes(raw)
                return array("H", struct.unpack("!%dH" % (len(raw) // 2), raw))
            assert self.bitdepth < 8
            width = self.width
            # Samples per byte
            spb = 8 // self.bitdepth
            out = array("B")
            mask = 2**self.bitdepth - 1
            shifts = [self.bitdepth * i for i in reversed(list(range(spb)))]
            for o in raw:
                out.extend(bytes([mask & (o >> i) for i in shifts]))
            return out[:width]

        return map(asvalues, rows)

    def serialtoflat(self, data, width=None):
        """Convert serial format (byte stream) pixel data to flat row
        flat pixel.
        """

        if self.bitdepth == 8:
            return data
        if self.bitdepth == 16:
            data = bytes(data)
            return array("H", struct.unpack("!%dH" % (len(data) // 2), data))
        assert self.bitdepth < 8
        if width is None:
            width = self.width
        # Samples per byte
        spb = 8 // self.bitdepth
        out = array("B")
        mask = 2**self.bitdepth - 1
        shifts = list(map(lambda x: x * self.bitdepth, reversed(list(range(spb)))))
        l = width
        for o in data:
            out.extend(bytes([(mask & (o >> s)) for s in shifts][:l]))
            l -= spb
            if l <= 0:
                l = width
        return out

    def iterstraight(self, raw):
        """Iterator that undoes the effect of filtering, and yields
        each row in serialised format (as a sequence of bytes).
        Assumes input is straightlaced.  `raw` should be an iterable
        that yields the raw bytes in chunks of arbitrary size.
        """

        # length of row, in bytes
        rb = self.row_bytes
        a = array("B")
        # The previous (reconstructed) scanline.  None indicates first
        # line of image.
        recon = None
        for some in raw:
            a.extend(some)
            a_index = 0
            while len(a) >= a_index + rb + 1:
                filter_type = a[a_index + 0]
                scanline = a[a_index + 1 : a_index + rb + 1]
                # del a[:rb+1]
                a_index += rb + 1
                recon = self.undo_filter(filter_type, scanline, recon)
                yield recon
        if len(a) != a_index:
            # :file:format We get here with a file format error:
            # when the available bytes (after decompressing) do not
            # pack into exact rows.
            raise FormatError("Wrong size for decompressed IDAT chunk")
        assert len(a) == a_index

    def validate_signature(self):
        """If signature (header) has not been read then read and
        validate it; otherwise do nothing.
        """

        if self.signature:
            return
        self.signature = self.file.read(8)
        if self.signature != _signature:
            raise FormatError("invalid signature")

    def preamble(self):
        """
        Extract the image metadata by reading the initial part of
        the PNG file up to the start of the ``IDAT`` chunk.  All the
        chunks that precede the ``IDAT`` chunk are read and either
        processed for metadata or discarded.
        """

        self.validate_signature()

        while True:
            if not self.atchunk:
                self.atchunk = self.chunklentype()
                if self.atchunk is None:
                    raise FormatError("no IDAT chunks")
            if self.atchunk[1] == b"IDAT":
                return
            self.process_chunk()

    def chunklentype(self):
        """Reads just enough of the input to determine the next
        chunk's length and type, returned as a (*length*, *type*) pair
        where *type* is a string.  If there are no more chunks, ``None``
        is returned.
        """

        x = self.file.read(8)
        if not x:
            return None
        if len(x) != 8:
            raise FormatError("EOF reading chunk length and type")
        length, type = struct.unpack("!I4s", x)
        if length > 2**31 - 1:
            raise FormatError("Chunk %s too large: %d" % (type, length))
        return length, type

    def process_chunk(self):
        """Process the next chunk and its data.  This only processes the
        following chunk types, all others are ignored: ``IHDR``,
        ``PLTE``, ``bKGD``, ``tRNS``, ``gAMA``, ``sBIT``, ``pHYs``.
        """

        type, data = self.chunk()
        method = "_process_" + str(type, "ascii")
        m = getattr(self, method, None)
        if m:
            m(data)

    def _process_IHDR(self, data):
        # http://www.w3.org/TR/PNG/#11IHDR
        if len(data) != 13:
            raise FormatError("IHDR chunk has incorrect length")
        (
            self.width,
            self.height,
            self.bitdepth,
            self.color_type,
            self.compression,
            self.filter,
            self.interlace,
        ) = struct.unpack("!2I5B", data)

        check_bitdepth_colortype(self.bitdepth, self.color_type)

        if self.compression != 0:
            raise Error("unknown compression method %d" % self.compression)
        if self.filter != 0:
            raise FormatError("Unknown filter method %d" % self.filter)
        if self.interlace not in (0, 1):
            raise FormatError("Unknown interlace method %d" % self.interlace)

        # Derived values
        # http://www.w3.org/TR/PNG/#6Colour-values
        colormap = bool(self.color_type & 1)
        greyscale = not self.color_type & 2
        alpha = bool(self.color_type & 4)
        color_planes = (3, 1)[greyscale or colormap]
        planes = color_planes + alpha

        self.colormap = colormap
        self.greyscale = greyscale
        self.alpha = alpha
        self.color_planes = color_planes
        self.planes = planes
        self.psize = float(self.bitdepth) / float(8) * planes
        if int(self.psize) == self.psize:
            self.psize = int(self.psize)
        self.row_bytes = int(math.ceil(self.width * self.psize))
        # Stores PLTE chunk if present, and is used to check
        # chunk ordering constraints.
        self.plte = None
        # NOTE: we no longer handle ancillary chunks
        # Stores tRNS chunk if present, and is used to check chunk
        # ordering constraints.
        # self.trns = None
        # Stores sbit chunk if present.
        # self.sbit = None

    def _process_PLTE(self, data):
        # http://www.w3.org/TR/PNG/#11PLTE
        if self.plte:
            raise FormatError("Multiple PLTE chunks present")
        self.plte = data
        if len(data) % 3 != 0:
            raise FormatError("PLTE chunk's length must be a multiple of 3")
        if len(data) > (2**self.bitdepth) * 3:
            raise FormatError("PLTE chunk is too long")
        if len(data) == 0:
            raise FormatError("Empty PLTE")

    def read(self):
        """
        Read the PNG file and decode it.  Returns (`width`, `height`,
        `pixels`, `metadata`).

        May use excessive memory.

        `pixels` are returned in boxed row flat pixel format.
        """

        def iteridat():
            """Iterator that yields all the ``IDAT`` chunks as strings."""
            while True:
                try:
                    type, data = self.chunk()
                except ValueError as e:
                    raise ChunkError(e.args[0])
                if type == b"IEND":
                    # http://www.w3.org/TR/PNG/#11IEND
                    break
                if type != b"IDAT":
                    continue
                # type == b'IDAT'
                # http://www.w3.org/TR/PNG/#11IDAT
                if self.colormap and not self.plte:
                    raise FormatError("PLTE chunk required before IDAT chunk")
                yield data

        def iterdecomp(idat):
            """Iterator that yields decompressed strings.  `idat` should
            be an iterator that yields the ``IDAT`` chunk data.
            """

            # Currently, with no max_length parameter to decompress,
            # this routine will do one yield per IDAT chunk: Not very
            # incremental.
            # d = zlib.decompress()
            # Each IDAT chunk is passed to the decompressor, then any
            # remaining state is decompressed out.
            alldata = b""
            for data in idat:
                alldata += data
                # :todo: add a max_length argument here to limit output
                # size.
                # yield array('B', d.decompress(data))
            # yield array('B', d.flush())
            yield decompress(alldata)

        self.preamble()
        raw = iterdecomp(iteridat())

        if self.interlace:
            raw = array("B", itertools.chain(*raw))
            arraycode = "BH"[self.bitdepth > 8]
            # Like :meth:`group` but producing an array.array object for
            # each row.
            pixels = map(
                lambda *row: array(arraycode, row),
                *[iter(self.deinterlace(raw))] * self.width * self.planes
            )
        else:
            pixels = self.iterboxed(self.iterstraight(raw))
        meta = dict()
        for attr in "greyscale alpha planes bitdepth interlace".split():
            meta[attr] = getattr(self, attr)
        meta["size"] = (self.width, self.height)
        for attr in "gamma transparent background".split():
            a = getattr(self, attr, None)
            if a is not None:
                meta[attr] = a
        if self.plte:
            meta["palette"] = self.palette()
        return self.width, self.height, pixels, meta

    def read_flat(self):
        """
        Read a PNG file and decode it into flat row flat pixel format.
        Returns (*width*, *height*, *pixels*, *metadata*).

        May use excessive memory.

        `pixels` are returned in flat row flat pixel format.

        See also the :meth:`read` method which returns pixels in the
        more stream-friendly boxed row flat pixel format.
        """

        x, y, pixel, meta = self.read()
        pixel = array("BH"[meta["bitdepth"] > 8], itertools.chain(*pixel))
        return x, y, pixel, meta

    def palette(self, alpha=False):
        """Returns a palette that is a sequence of 3-tuples or 4-tuples,
        synthesizing it from the ``PLTE`` and ``tRNS`` chunks.  These
        chunks should have already been processed (for example, by
        calling the :meth:`preamble` method).  All the tuples are the
        same size: 3-tuples if there is no ``tRNS`` chunk, 4-tuples when
        there is a ``tRNS`` chunk.  Assumes that the image is colour type
        3 and therefore a ``PLTE`` chunk is required.

        If the `alpha` argument is ``True`` then an alpha channel is
        always added, forcing the result to be a sequence of 4-tuples.
        """

        if not self.plte:
            raise FormatError("No PLTE in indexed image")
        plte = group(array("B", self.plte), 3)
        if alpha:
            trns = array("B", [])
            trns.extend(b"\xff" * (len(plte) - len(trns)))
            plte = list(map(lambda x, y: x + y, plte, group(trns, 1)))
        return plte

    def asDirect(self):
        """Returns the image data as a direct representation of an
        ``x * y * planes`` array.  This method is intended to remove the
        need for callers to deal with palettes and transparency
        themselves.  Images with a palette (colour type 3)
        are converted to RGB or RGBA; images with transparency (a
        ``tRNS`` chunk) are converted to LA or RGBA as appropriate.
        When returned in this format the pixel values represent the
        colour value directly without needing to refer to palettes or
        transparency information.

        Like the :meth:`read` method this method returns a 4-tuple:

        (*width*, *height*, *pixels*, *meta*)

        This method normally returns pixel values with the bit depth
        they have in the source image, but when the source PNG has an
        ``sBIT`` chunk it is inspected and can reduce the bit depth of
        the result pixels; pixel values will be reduced according to
        the bit depth specified in the ``sBIT`` chunk (PNG nerds should
        note a single result bit depth is used for all channels; the
        maximum of the ones specified in the ``sBIT`` chunk.  An RGB565
        image will be rescaled to 6-bit RGB666).

        The *meta* dictionary that is returned reflects the `direct`
        format and not the original source image.  For example, an RGB
        source image with a ``tRNS`` chunk to represent a transparent
        colour, will have ``planes=3`` and ``alpha=False`` for the
        source image, but the *meta* dictionary returned by this method
        will have ``planes=4`` and ``alpha=True`` because an alpha
        channel is synthesized and added.

        *pixels* is the pixel data in boxed row flat pixel format (just
        like the :meth:`read` method).

        All the other aspects of the image data are not changed.
        """

        self.preamble()

        # Simple case, no conversion necessary.
        if not self.colormap:
            return self.read()

        x, y, pixels, meta = self.read()

        if self.colormap:
            meta["colormap"] = False
            meta["alpha"] = False
            meta["bitdepth"] = 8
            meta["planes"] = 3 + False
            plte = self.palette()

            def iterpal(pixels):
                for row in pixels:
                    row = [plte[x] for x in row]
                    yield array("B", itertools.chain(*row))

            pixels = iterpal(pixels)
        return x, y, pixels, meta

    def _as_rescale(self, get, targetbitdepth):
        """Helper used by :meth:`asRGB8` and :meth:`asRGBA8`."""

        width, height, pixels, meta = get()
        maxval = 2 ** meta["bitdepth"] - 1
        targetmaxval = 2**targetbitdepth - 1
        factor = float(targetmaxval) / float(maxval)
        meta["bitdepth"] = targetbitdepth

        def iterscale():
            for row in pixels:
                yield [int(round(x * factor)) for x in row]

        if maxval == targetmaxval:
            return width, height, pixels, meta
        else:
            return width, height, iterscale(), meta

    def asRGB8(self):
        """Return the image data as an RGB pixels with 8-bits per
        sample.  This is like the :meth:`asRGB` method except that
        this method additionally rescales the values so that they
        are all between 0 and 255 (8-bit).  In the case where the
        source image has a bit depth < 8 the transformation preserves
        all the information; where the source image has bit depth
        > 8, then rescaling to 8-bit values loses precision.  No
        dithering is performed.  Like :meth:`asRGB`, an alpha channel
        in the source image will raise an exception.

        This function returns a 4-tuple:
        (*width*, *height*, *pixels*, *metadata*).
        *width*, *height*, *metadata* are as per the
        :meth:`read` method.

        *pixels* is the pixel data in boxed row flat pixel format.
        """

        return self._as_rescale(self.asRGB, 8)

    def asRGBA8(self):
        """Return the image data as RGBA pixels with 8-bits per
        sample.  This method is similar to :meth:`asRGB8` and
        :meth:`asRGBA`:  The result pixels have an alpha channel, *and*
        values are rescaled to the range 0 to 255.  The alpha channel is
        synthesized if necessary (with a small speed penalty).
        """

        return self._as_rescale(self.asRGBA, 8)

    def asRGB(self):
        """Return image as RGB pixels.  RGB colour images are passed
        through unchanged; greyscales are expanded into RGB
        triplets (there is a small speed overhead for doing this).

        An alpha channel in the source image will raise an
        exception.

        The return values are as for the :meth:`read` method
        except that the *metadata* reflect the returned pixels, not the
        source image.  In particular, for this method
        ``metadata['greyscale']`` will be ``False``.
        """

        width, height, pixels, meta = self.asDirect()
        if meta["alpha"]:
            raise Error("cannot convert image with alpha channel to RGB")
        if not meta["greyscale"]:
            return width, height, pixels, meta
        meta["greyscale"] = False
        typecode = "BH"[meta["bitdepth"] > 8]

        def iterrgb():
            for row in pixels:
                a = array(typecode, [0]) * 3 * width
                for i in range(3):
                    a[i::3] = row
                yield a

        return width, height, iterrgb(), meta

    def asRGBA(self):
        """Return image as RGBA pixels.  Greyscales are expanded into
        RGB triplets; an alpha channel is synthesized if necessary.
        The return values are as for the :meth:`read` method
        except that the *metadata* reflect the returned pixels, not the
        source image.  In particular, for this method
        ``metadata['greyscale']`` will be ``False``, and
        ``metadata['alpha']`` will be ``True``.
        """

        width, height, pixels, meta = self.asDirect()
        if meta["alpha"] and not meta["greyscale"]:
            return width, height, pixels, meta
        typecode = "BH"[meta["bitdepth"] > 8]
        maxval = 2 ** meta["bitdepth"] - 1
        # maxbuffer = struct.pack('=' + typecode, maxval) * 4 * width
        maxbuffer = struct.pack("!" + typecode, maxval) * 4 * width

        if meta["alpha"] and meta["greyscale"]:
            # LA to RGBA
            def convert():
                for row in pixels:
                    # Create a fresh target row, then copy L channel
                    # into first three target channels, and A channel
                    # into fourth channel.
                    a = array(typecode, maxbuffer)
                    pngfilters.convert_la_to_rgba(row, a)
                    yield a

        elif meta["greyscale"]:
            # L to RGBA
            def convert():
                for row in pixels:
                    a = array(typecode, maxbuffer)
                    pngfilters.convert_l_to_rgba(row, a)
                    yield a

        else:
            assert not meta["alpha"] and not meta["greyscale"]

            # RGB to RGBA
            def convert():
                for row in pixels:
                    a = array(typecode, maxbuffer)
                    pngfilters.convert_rgb_to_rgba(row, a)
                    yield a

        meta["alpha"] = True
        meta["greyscale"] = False
        return width, height, convert(), meta


def check_bitdepth_colortype(bitdepth, colortype):
    """Check that `bitdepth` and `colortype` are both valid,
    and specified in a valid combination. Returns if valid,
    raise an Exception if not valid.
    """

    if bitdepth not in (1, 2, 4, 8, 16):
        raise FormatError("invalid bit depth %d" % bitdepth)
    if colortype not in (0, 2, 3, 4, 6):
        raise FormatError("invalid colour type %d" % colortype)
    # Check indexed (palettized) images have 8 or fewer bits
    # per pixel; check only indexed or greyscale images have
    # fewer than 8 bits per pixel.
    if colortype & 1 and bitdepth > 8:
        raise FormatError(
            "Indexed images (colour type %d) cannot have bidepth"
            " > 8 (bit depth %d)" % (bitdepth, colortype)
        )
    if bitdepth < 8 and colortype not in (0, 3):
        raise FormatError(
            "Illegal combination of bit depth %d and colour"
            " type %d." % (bitdepth, colortype)
        )


# def isinteger(x):
#    try:
#        return int(x) == x
#    except (TypeError, ValueError):
#        return False


class pngfilters:
    @staticmethod
    def undo_filter_sub(filter_unit, scanline, previous, result):
        """Undo sub filter."""

        ai = 0
        # Loops starts at index fu.  Observe that the initial part
        # of the result is already filled in correctly with
        # scanline.
        for i in range(filter_unit, len(result)):
            x = scanline[i]
            a = result[ai]
            result[i] = (x + a) & 0xFF
            ai += 1

    @staticmethod
    def undo_filter_up(filter_unit, scanline, previous, result):
        """Undo up filter."""

        for i in range(len(result)):
            x = scanline[i]
            b = previous[i]
            result[i] = (x + b) & 0xFF

    @staticmethod
    def undo_filter_average(filter_unit, scanline, previous, result):
        """Undo up filter."""

        ai = -filter_unit
        for i in range(len(result)):
            x = scanline[i]
            if ai < 0:
                a = 0
            else:
                a = result[ai]
            b = previous[i]
            result[i] = (x + ((a + b) >> 1)) & 0xFF
            ai += 1

    @staticmethod
    def undo_filter_paeth(filter_unit, scanline, previous, result):
        """Undo Paeth filter."""

        # Also used for ci.
        ai = -filter_unit
        for i in range(len(result)):
            x = scanline[i]
            if ai < 0:
                a = c = 0
            else:
                a = result[ai]
                c = previous[ai]
            b = previous[i]
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                pr = a
            elif pb <= pc:
                pr = b
            else:
                pr = c
            result[i] = (x + pr) & 0xFF
            ai += 1

    @staticmethod
    def convert_la_to_rgba(row, result):
        for i in range(3):
            # result[i::4] = row[0::2]
            for item, dest in zip(
                itertools.islice(row, 0, len(row), 2), range(i, len(result), 4)
            ):
                result[dest] = item
        # result[3::4] = row[1::2]
        for item, dest in zip(
            itertools.islice(row, 1, len(row), 2), range(3, len(result), 4)
        ):
            result[dest] = item

    @staticmethod
    def convert_l_to_rgba(row, result):
        """Convert a grayscale image to RGBA. This method assumes
        the alpha channel in result is already correctly
        initialized.
        """
        for i in range(3):
            # result[i::4] = row
            for item, dest in zip(row, range(i, len(result), 4)):
                result[dest] = item

    @staticmethod
    def convert_rgb_to_rgba(row, result):
        """Convert an RGB image to RGBA. This method assumes the
        alpha channel in result is already correctly initialized.

        for i in range(3):
            #result[i::4] = row[i::3]
            for item, dest in zip(itertools.islice(row, i, len(row), 3),
                                  range(i, len(result), 4)):
                result[dest] = item
        """
        for i in range(len(row) // 3):
            for j in range(3):
                result[i * 4 + j] = row[i * 3 + j]


def getPNG(fn, key):
    saved = machine.freq()
    machine.freq(240000000)
    png_reader = Reader(filename=fn)
    image_data = png_reader.asRGBA8()
    w = image_data[0]
    h = image_data[1]
    f = framebuf.FrameBuffer(bytearray(w * h * 2), w, h, framebuf.RGB565)
    f.fill(key)
    r = 0
    for row in image_data[2]:
        for c in range(0, w):
            pos = c * 4
            col = rgb(row[pos], row[pos + 1], row[pos + 2])
            if not col == key:
                f.pixel(c, r, col)
        r += 1
    machine.freq(saved)
    return (w, h, f, key)


def saveRaw(fn, fnout):
    saved = machine.freq()
    machine.freq(240000000)
    png_reader = Reader(filename=fn)
    image_data = png_reader.asRGBA8()
    w = image_data[0]
    h = image_data[1]
    rowbuf = bytearray(w * 2)
    f = framebuf.FrameBuffer(rowbuf, w, 1, framebuf.RGB565)
    fo = open(fnout, "wb")
    for row in image_data[2]:
        for c in range(0, w):
            pos = c * 4
            col = rgb(row[pos], row[pos + 1], row[pos + 2])
            f.pixel(c, 0, col)
        fo.write(rowbuf)
    fo.close()
    machine.freq(saved)


def drawPNG(im, x, y):
    global g
    g.updateMod(x, y, x + im[0] - 1, y + im[1] - 1)
    g.blit(im[2], x, y, im[3])
