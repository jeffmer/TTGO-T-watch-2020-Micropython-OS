from tempos import g
import loader
from graphics import rgb,WHITE,BLACK,GREY,RED,GREEN,LIGHTGREY
from fonts import roboto24,roboto36
from button import RoundButton,ButtonMan,Theme
from drivers.l67k import L67K
import json

gps = L67K()

postheme = Theme(WHITE,LIGHTGREY,GREEN,LIGHTGREY,roboto24)

update = RoundButton("Update",10,120,100,50,theme=postheme)
cancel = RoundButton("Cancel",10,180,100,50,theme=postheme)
save   = RoundButton("Save",140,180,100,50,theme=postheme)

buttons = ButtonMan()
buttons.add(update)
buttons.add(cancel)
buttons.add(save)


def drawPos():
    global gps
    g.setfont(roboto24)
    if not gps._pos is None:
        g.setfontalign(-1,-1)
        g.text("Lat : {:.4f}".format(gps._pos[0]),60,60,WHITE)
        g.text("Long: {:.4f}".format(gps._pos[1]),60,90,WHITE)
    else:
        g.setfontalign(0,-1)
        if not gps.updating():
            g.text("Unknown",120,90,RED)
        else:
            g.text("Updating",120,90,GREEN)
            
            
def doupdate():
    gps.update()
    loader.jump_to("position")
    
def docancel():
    gps.cancel_update()
    loader.jump_to("position")

def dosave():
    loader.jump_to("position")
    if not gps._pos is None:
        s = json.dumps({"lat":gps._pos[0],"long":gps._pos[1]})
        with open("location.json","w") as f:
            f.write(s)
            f.close()
        print(s)
    
update.callback(doupdate)
cancel.callback(docancel)
save.callback(dosave)

def onUpdate(pos):
    loader.jump_to("position")

gps.addListener(onUpdate)

def app_init():
    g.setfont(roboto36)
    g.setfontalign(0,-1)
    g.text("Position",120,10,WHITE)
    drawPos()
    buttons.start()
  
def app_end():
    buttons.stop()
    g.fill(BLACK)