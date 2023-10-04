from micropython import const
from tempos import tc, prtc, sched, pm, SWIPE_RIGHT, SWIPE_LEFT, SWIPE_DOWN, SWIPE_UP
import os
import apps
import utils
import clocks


class Ring:
    "class used to handle the switch from one app to another in a ring configuration"
    def __init__(self, parent):
        self.ring = []
        self.names = []
        self.curr = 0
        parentname = getattr(parent, "__name__")
        appslist = os.listdir(parentname)
        for f in appslist:
            mm = f.split(".")[0]
            try:
                __import__(parentname + "." + mm)
                self.names.append(mm)
                self.ring.append(getattr(parent, mm))
            except Exception as e:
                print("{} : {} : {}".format(mm, type(e).__name__, e))

    def mod(self, a):
        n = len(self.ring)
        return a - n if a >= n else a + n if a < 0 else a

    def call(self, i, start):
        if i < 0 or i >= len(self.ring):
            return
        try:
            if start:
                self.ring[i].app_init()
            else:
                self.ring[i].app_end()
        except Exception as e:
            print("{} : {} : {}".format(self.names[i], type(e).__name__, e))

    def begin(self):
        if len(self.ring) == 0:
            return
        self.call(self.curr, True)

    def end(self):
        if len(self.ring) == 0:
            return
        self.call(self.curr, False)

    def switch(self, inc):
        nxt = self.mod(self.curr + inc)
        if nxt == self.curr:
            return
        self.end()
        self.curr = nxt
        self.begin()

    def find(self, name):
        try:
            return self.names.index(name)
        except:
            return -1


def changelevel(dir):
    global level, rings
    oldlevel = level
    level += dir
    if level < 0 or level >= len(rings):
        level = oldlevel
    else:
        rings[oldlevel].end()
        rings[level].begin()


_APP_LOCK = False


def setapplock(b):
    global _APP_LOCK
    _APP_LOCK = b


def getscreen():
    global rings, level
    rings[level].end()
    setapplock(True)


def relscreen():
    global rings, level
    rings[level].begin()
    setapplock(False)


APPLEVEL = const(0)
CLOCKLEVEL = const(1)
UTILLEVEL = const(2)
appRing = Ring(apps)
utilRing = Ring(utils)
clockRing = Ring(clocks)
rings = (appRing, clockRing, utilRing)
level = 1


def jump_to(newlevel, app):
    global level, rings
    res = rings[newlevel].find(app)
    if res < 0:
        return
    else:
        setapplock(False)
        rings[level].end()
        utilRing.curr = res
        level = newlevel
        rings[level].begin()


def touched(tch):
    global level, _APP_LOCK
    if _APP_LOCK:
        return
    if tch[2] == SWIPE_RIGHT:
        rings[level].switch(1)
    elif tch[2] == SWIPE_LEFT:
        rings[level].switch(-1)
    elif tch[2] == SWIPE_DOWN:
        changelevel(1)
    elif tch[2] == SWIPE_UP:
        changelevel(-1)


def makesafe(tch):
    sched.setTimeout(10, touched, tch)


def alarmsafe(dummy):
    state,_,_ = prtc.read_alarm()
    if state == 2:
        sched.setTimeout(10, jump_to, UTILLEVEL, "alarm")


touch = tc.addListener(makesafe)
alarm = prtc.addListener(alarmsafe)
malarm = pm.addListener(alarmsafe)

rings[level].begin()
sched.run()
