from tempos import g
from graphics import WHITE,BLACK,YELLOW
from fonts import roboto18,roboto24,roboto36
from button import Button,ButtonMan
import time
from widgets import Label
from wifi import do_connected_action
from urequests import  request
import math
import json
import os
from apps.maps import get_location

status = Label(10,80,180,40,roboto24,YELLOW)
progress = Label(200,80,40,40,roboto24,YELLOW)

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def fetchtile(x,y,zoom,f):
    global resp
    url = "https://tile.openstreetmap.de/{}/{}/{}.png".format(zoom,x,y)
    resp = request("GET",url)
    if resp.status_code==200:
        f.write(resp.content)
        f.close()
    return resp.status_code==200

def centre_text(str,font,x,y,c):
    global g
    g.setfont(font)
    g.setfontalign(0,-1)
    g.text(str,x,y,c)

def makelevel(zoom):
    try:
        os.mkdir("/sd/tiles/{}".format(zoom))
    except:
        pass

def makedir(tilex,zoom):
    try:
        os.mkdir("/sd/tiles/{}/{}".format(zoom,tilex))
    except:
        pass
        
def openfile(tilex,tiley,zoom):
    try:
        return open("/sd/tiles/{}/{}/{}.png".format(zoom,tilex,tiley),'xb')
    except:
        return None

def getTiles():
    count=0
    loc,zoom = get_location()
    makelevel(zoom)
    xy = deg2num(loc[0],loc[1],zoom)
    for y in range(-1,2):
        for x in range(-1,2):
            tilex = xy[0]+x; tiley = xy[1]+y
            status.update("{}.{}".format(tilex,tiley))
            makedir(tilex,zoom)
            f = openfile(tilex,tiley,zoom)
            if not f is None:
                resp = fetchtile(tilex,tiley,zoom,f)
                count+=1
                progress.update(str(count))
            else:
                progress.update("C")
           
def get_tiles():
    global status,progress
    do_connected_action(getTiles,status,progress)
    
def gen_map():
    gen_raw__tiles()
    combine_tiles()
   
update = Button("Fetch",80,180,80,40,roboto24)
buttons = ButtonMan()
buttons.add(update)
update.callback(get_tiles)

def app_init():
    global buttons
    centre_text("OSM Tiles",roboto36,120,4,WHITE)
    status.update('Idle')
    progress.update('')
    buttons.start()

def app_end():
    buttons.stop()
    g.fill(BLACK)