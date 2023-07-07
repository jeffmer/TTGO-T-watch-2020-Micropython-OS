from tempos import g, tc, WHITE, TOUCH_DOWN


def drawMarks():
    g.ellipse(20, 20, 3, 3, WHITE, True)
    g.ellipse(220, 20, 3, 3, WHITE, True)
    g.ellipse(20, 220, 3, 3, WHITE, True)
    g.ellipse(220, 220, 3, 3, WHITE, True)
    g.show()


def ontouch(tch):
    if tch[2] == TOUCH_DOWN:
        print("touch", tch[0], tch[1])


drawMarks()
tc.addListener(ontouch)
