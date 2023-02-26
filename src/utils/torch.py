from tempos import pm,g,sched,WHITE,BLACK,settings
from loader import getscreen,relscreen
from fonts import roboto36,roboto24

def torch(v):
    if v:
        getscreen()
        g.fill(WHITE)
        g.show()
        g.bright(1)
    else:
        g.fill(BLACK)
        g.show()
        g.bright(settings.brightness)
        relscreen()

torchon = False
clickno = 0

def onclick(d):
    global clickno,torchon
    def resetClick():
        global clickno
        clickno = 0
    clickno+=1
    if clickno==2:
        torchon = not torchon
        torch(torchon)
        resetClick()
    else:
        sched.setTimeout(500,resetClick)
 
pm.addListener(onclick)


def app_end():
    g.fill(BLACK)
    
def app_init():
    g.setfont(roboto36)
    g.setfontalign(0,-1)
    g.text("Torch",120,20,WHITE)
    g.setfontalign(-1,-1)
    g.setfont(roboto24)
    g.wordwraptext("Turn on torch from any screen by double clicking on button.",20,80,220,WHITE)
    g.show()