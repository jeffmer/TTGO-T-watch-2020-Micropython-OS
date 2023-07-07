N = 5
outfile = open("/home/jeff/tiles/ham.raw", "wb")
# outbuf = bytearray(512*256*N*N)
# outpos = 0

for row in range(N):
    files = []
    for i in range(N):
        fn = "/home/jeff/tiles/t{}.raw".format(row * N + i)
        print(fn)
        files.append(open(fn, "rb"))

    for y in range(256):
        for x in range(N):
            pos = files[x].seek(y * 512)
            buf = files[x].read(512)
            # outbuf[outpos:outpos+512]=buf
            # outpos+=512
            outfile.write(buf)

    for i in range(N):
        files[i].close()

outfile.close()
