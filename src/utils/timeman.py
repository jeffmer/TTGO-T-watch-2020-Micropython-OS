from micropython import const
from tempos import g, sched, set_local_time, rtc, prtc, settings
from graphics import rgb, WHITE, BLACK, YELLOW
from fonts import roboto24, roboto36
from button import Button, RoundButton, ButtonMan
from wifi import do_connected_action
import ntptime
from widgets import ValueDisplay, Label, SwitchPanel

# time zone adjustment
dst = False


def zadjust(incr):
    settings.timezone += incr
    return settings.timezone


def changedst(v):
    settings.dst = v


buttons = ButtonMan()
zone = ValueDisplay("Time Zone", 2, False, 1, zadjust, buttons)
dst = SwitchPanel("Summer Time", 102, settings.dst, changedst, buttons)

# time synchronisation

status = Label(20, 200, 160, 40, roboto24, YELLOW)
progress = Label(200, 200, 40, 40, roboto24, YELLOW)


def dosync():
    ntptime.settime()
    prtc.set_datetime(rtc.datetime())
    set_local_time()


def button_action():
    do_connected_action(dosync, status, progress)


start = Button("Sync with NTP", 20, 160, 200, 40, theme=ValueDisplay.theme)
buttons.add(start)
start.callback(button_action)


def app_init():
    zone.drawInit(settings.timezone)
    status.update("Idle", False)
    progress.update("", False)
    buttons.start()


def app_end():
    settings.save()
    buttons.stop()
    g.fill(BLACK)
    set_local_time()
