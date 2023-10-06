from tempos import g, settings, WHITE, BLACK
from widgets import SwitchPanel
from button import ButtonMan
from fonts import roboto24, roboto36


def changeclick(v):
    settings.clicking = v


def changebuzz(v):
    settings.buzzing = v
    
def changeflash(v):
    settings.flashing =v


buttons = ButtonMan()
clicking = SwitchPanel("Click on Touch", 55, settings.clicking, changeclick, buttons)
buzzing = SwitchPanel("Buzz on Alarm", 110, settings.buzzing, changebuzz, buttons)
flashing = SwitchPanel("Flash on Alarm", 165, settings.flashing, changeflash, buttons)


def app_init():
    g.setfont(roboto36)
    g.setfontalign(0, -1)
    g.text("Buzzer", 120, 10, WHITE)
    buttons.start()


def app_end():
    settings.save()
    buttons.stop()
    g.fill(BLACK)
