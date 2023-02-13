from micropython import const
from tempos import g,sched,set_local_time,rtc,prtc,settings
from graphics import rgb,WHITE,BLACK,YELLOW
from fonts import roboto24,roboto36
from button import Button,RoundButton,ButtonMan
from wifi import do_connected_action
import ntptime
from widgets import ValueDisplay, Label

# time zone adjustment

def zadjust(incr):
    settings.timezone += incr
    return settings.timezone

buttons = ButtonMan()
zone = ValueDisplay("Time Zone",15,False,1,zadjust,buttons)

# time synchronisation

status = Label(20,200,160,40,roboto24,WHITE)
progress = Label(200,200,40,40,roboto24,WHITE)

def dosync():
    ntptime.settime()
    prtc.set_datetime(rtc.datetime())
    set_local_time()

def button_action():
    do_connected_action(dosync,status,progress)


start = RoundButton("Sync",80,160,80,40,theme=ValueDisplay.theme)
buttons.add(start)
start.callback(button_action)

def app_init():
    zone.drawInit(settings.timezone)
    g.setfont(roboto36)
    title = "Sync Time"
    ll = roboto36.get_width(title)
    g.text(title,(240-ll)//2,115,WHITE)
    status.update('Idle',False)
    progress.update('',False)
    buttons.start()
    
def app_end():
    buttons.stop()
    g.fill(BLACK)
    set_local_time()
