from micropython import const
from tempos import g, sched
from graphics import rgb, WHITE, BLACK, GREEN, GREY
from fonts import roboto24, roboto36
from button import Theme, RoundButton, ButtonMan
import math

ORANGE = rgb(0xF1, 0xC2, 0x71)  # f1c271
LIGHTGREY = rgb(200, 200, 200)

nu_theme = Theme(WHITE, LIGHTGREY, GREEN, LIGHTGREY, roboto24)
op_theme = Theme(WHITE, ORANGE, GREEN, ORANGE, roboto24)

DX = 4 if g.width<=240 else 44
CY = g.width//2

def get_theme(s):
    global nu_theme, op_theme
    if s in "0123456789.":
        return nu_theme
    else:
        return op_theme


fields = "789+(" "456-)" "123*^" "C0./="

buttons = ButtonMan()

output = ""


def drawOutput(now=True):
    global output
    g.fill_rect(DX, 0, 232, 40, GREY)
    g.setfont(roboto36)
    g.setfontalign(0, -1)
    g.text(output, CY, 2, WHITE)
    if now:
        g.show()


def action(s):
    global output
    if s == "C":
        output = ""
    elif s == "=":
        try:
            output = str(eval(output.replace("^", "**")))[:12]
        except:
            output = "Error"
    else:
        output += s
    drawOutput()


for j in range(0, 4):
    for i in range(0, 5):
        s = fields[j * 5 + i]
        b = RoundButton(s, i * 48 + DX, (j + 1) * 48 + 4, 40, 40, theme=get_theme(s))
        buttons.add(b)
        b.callback(action, s)


def app_init():
    global buttons
    drawOutput(False)
    buttons.start()


def app_end():
    buttons.stop()
    g.fill(BLACK)
