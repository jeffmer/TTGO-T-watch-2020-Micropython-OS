from tempos import g,settings,json
from graphics import WHITE,BLACK,YELLOW
from fonts import roboto18,roboto24,roboto36
from button import Button,ButtonMan
import time
import png
from widgets import Label
from wifi import do_connected_action
from urequests import  request
from config import OWP_KEY
from config import VERSION
if VERSION == 2:
    from apps.maps import get_location 

status = Label(0,200,100,30,roboto18,YELLOW)
progress = Label(110,200,30,30,roboto18,YELLOW)

display = {
    'place':'xxx,CC',
    'desc' :'description',
    'icon' :'unknown',
    'temp' :'00.0C',
    'humid':'00%',
    'press':'1000mb',
    'wind' :'0.0mph S',
    'rise' :'Sunrise 0:00',
    'set'  :'Sunset  0:00'
}

displayicon = png.getPNG('images/weather/unknown.png',WHITE)

def deg_to_dir(d):
    dirs = ('N','NE','E','SE','S','SW','W','NW')
    dr = (d+22)//45
    if dr>7:
        dr = 0
    return dirs[dr] 

def secs_to_time(secs,zone):
    lsecs = secs + zone*3600 + (3600 if settings.dst else 0) - 946684800
    loctime =   time.gmtime(lsecs)
    return '{:2d}:{:02}'.format(loctime[3],loctime[4])

def updateDisplay(dd):
    global displayicon
    display['place'] = dd['name']+', '+dd['sys']['country']
    display['desc']  = dd['weather'][0]['description']
    if not (display['icon'] == dd['weather'][0]['icon']):
        icon  = dd['weather'][0]['icon']
        displayicon = png.getPNG('images/weather/'+icon+'.png',WHITE)
        display['icon'] = icon
    display['temp'] = '{:.1f} C'.format(dd['main']['temp']-273)
    display['humid'] = '{:d}%'.format(dd['main']['humidity'])
    display['press'] = '{:d}mb'.format(dd['main']['pressure'])
    display['wind'] = '{:.1f}mph {:s}'.format(dd['wind']['speed'],deg_to_dir(dd['wind']['deg']))
    display['rise'] = 'Sunrise ' + secs_to_time(dd['sys']['sunrise'],dd['timezone'])
    display['set']  = 'Sunset ' + secs_to_time(dd['sys']['sunset'],dd['timezone'])

def centre_text(str,font,x,y,c):
    global g
    g.setfont(font)
    g.setfontalign(0,-1)
    g.text(str,x,y,c)

def drawDisplay():
    g.fill_rect(0,0,240,200,BLACK)
    centre_text(display['place'],roboto36,120,4,WHITE)
    centre_text(display['desc'],roboto18,120,40,WHITE)
    g.fill_rect(140,70,96,96,WHITE) 
    png.drawPNG(displayicon,140,70)
    xoffset = 10
    g.setfontalign(-1,-1)
    g.setfont(roboto36)
    g.text(display['temp'],xoffset,60,WHITE)
    g.setfont(roboto18)
    g.text(display['humid'],xoffset,95,WHITE)
    g.text(display['press'],xoffset,115,WHITE)
    g.text(display['wind'],xoffset,135,WHITE)
    g.text(display['rise'],xoffset,160,WHITE)
    g.text(display['set'],xoffset,180,WHITE)
    g.show()

def getupdate():
    if VERSION == 2:
        loc,_ = get_location()
    else:
        home = json.loads(open("location.json").read())
        loc = (home["lat"],home["long"])
    url = "https://api.openweathermap.org/data/2.5/weather?lat={:.3f}&lon={:.3f}&appid={}".format(loc[0],loc[1],OWP_KEY)
    r = request("GET",url)
    dd = r.json()
    # 401 code: invalid api key
    if dd['cod']==200:
        try:
            updateDisplay(dd)
            drawDisplay()
        except Exception as err:
            status.update("{}:{}".format(dd['cod'], str(err)))
    else:
        print(dd)

def get_weather():
    global status,progress
    do_connected_action(getupdate,status,progress)
   
update = Button("Update",160,200,60,30,roboto18)
buttons = ButtonMan()
buttons.add(update)
update.callback(get_weather)

def app_init():
    global buttons
    drawDisplay()
    status.update('Idle')
    progress.update('')
    buttons.start()

def app_end():
    buttons.stop()
    g.fill(BLACK)