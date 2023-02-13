import png
import sys

WIDTH = 240
HEIGHT = 240

# convert row of  rgb565 to rgb
def convert_row(rowin):
    global WIDTH
    rowout = bytearray(WIDTH*3)
    for i in range(0,WIDTH):
        rowout[i*3] = (rowin[i*2] & 0xF8) 
        rowout[i*3+1] = (((rowin[i*2] & 0x07)<<5) | ((rowin[i*2+1] & 0xE0)>>3)) 
        rowout[i*3+2] = ((rowin[i*2+1] & 0x1F)<<3) 
    return rowout


def main(fname):
    global HEIGHT,WIDTH
    rgbbuf = []
    names = fname.split('.')
    with open(fname,"rb") as raw:
        inbuf = raw.read()
        raw.close()
    for i in range(0,HEIGHT*WIDTH*2,HEIGHT*2):
        rgbbuf.append(convert_row(inbuf[i:i+WIDTH*2]))
    png_writer = png.Writer(WIDTH,HEIGHT,greyscale=False)
    with open(names[0]+".png","wb") as pngfile:
        png_writer.write(pngfile,rgbbuf)
        pngfile.close()

if __name__ == "__main__":
    args = sys.argv
    main(args[1]);
