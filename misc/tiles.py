import math
from time import sleep
from requests import request


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    n = 2.0**zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


def fetchtile(x, y, zoom, fn):
    url = "https://tile.openstreetmap.de/{}/{}/{}.png".format(zoom, x, y)
    resp = request("GET", url)
    if resp.ok:
        with open(fn, "wb") as f:
            f.write(resp.content)
            f.close()
    return resp.ok


loc = deg2num(51.4370, -0.3198, 16)
print(loc)

count = 0
for y in range(-1, 2):
    for x in range(-1, 2):
        tilex = loc[0] + x
        tiley = loc[1] + y
        resp = fetchtile(tilex, tiley, 16, "/home/jeff/tiles/t{}.png".format(count))
        print(tilex, tiley, count, resp)
        count += 1
        sleep(2)
