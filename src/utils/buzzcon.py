from tempos import g,settings,WHITE,BLACK
from widgets import SwitchPanel
from button import ButtonMan
from fonts import roboto24,roboto36

def changeclick(v):
    settings.clicking = v

def changebuzz(v):
    settings.buzzing = v

buttons = ButtonMan()
clicking = SwitchPanel("Click on Touch",60,settings.clicking,changeclick,buttons)
buzzing = SwitchPanel("Buzz on Alarm",130,settings.buzzing,changebuzz,buttons)

def app_init():
    g.setfont(roboto36)
    title = "Buzzer"
    ll = g.getfont().get_width(title)
    g.text(title,(240-ll)//2,10,WHITE)
    buttons.start()
    
def app_end():
    buttons.stop()
    g.fill(BLACK)