from tempos import g, settings, BLACK
from button import ButtonMan
from widgets import ValueDisplay


def badjust(incr):
    settings.brightness += incr
    g.bright(settings.brightness)
    return settings.brightness


def oadjust(incr):
    settings.ontime += incr
    return settings.ontime


buttons = ButtonMan()
bright = ValueDisplay("Brightness", 15, True, 0.1, badjust, buttons)
ontime = ValueDisplay("On Time", 125, False, 5, oadjust, buttons)


def app_init():
    bright.drawInit(settings.brightness)
    ontime.drawInit(settings.ontime)
    buttons.start()


def app_end():
    settings.save()
    buttons.stop()
    g.fill(BLACK)
