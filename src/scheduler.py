import micropython
import machine
from time import ticks_ms, ticks_add, ticks_diff, sleep_ms


class Entry:
    def __init__(self, action, arg, delay=0, repeat=False, time=0):
        self.action = action
        self.arg = arg
        self.delay = delay
        self.repeat = repeat
        self.time = time


class Event:
    def __init__(self):
        self.queue = []

    def signal(self, arg):
        for e in self.queue:
            e.action(arg)

    def irq_signal(self, arg):
        micropython.schedule(self.signal, arg)

    def addListener(self, act):
        e = Entry(act, 0)
        self.queue.append(e)
        return e

    def removeListener(self, e):
        i = 0
        while i < len(self.queue) and not e is self.queue[i]:
            i = i + 1
        if i < len(self.queue):
            self.queue.pop(i)


class Scheduler:
    def __init__(self):
        self.queue = []
        self.next = None

    def _insert(self, e):
        i = 0
        while i < len(self.queue) and ticks_diff(e.time, self.queue[i].time) >= 0:
            i = i + 1
        self.queue.insert(i, e)

    def _remove(self, e):
        i = 0
        while i < len(self.queue) and not e is self.queue[i]:
            i = i + 1
        if i < len(self.queue):
            self.queue.pop(i)

    def _schedule(self, e):
        if len(self.queue) > 0 and ticks_diff(self.queue[0].time, ticks_ms()) <= 0:
            self.next = self.queue[0]
            self.queue.pop(0)
            if self.next.repeat:
                self.next.time = self.next.delay + ticks_ms()
                self._insert(self.next)
        else:
            self.next = None

    def setInterval(self, period, act, *arg):
        entry = Entry(act, arg, period, True, ticks_add(ticks_ms(), period))
        self._insert(entry)
        return entry

    def setTimeout(self, period, act, *arg):
        entry = Entry(act, arg, period, False, ticks_add(ticks_ms(), period))
        self._insert(entry)
        return entry

    def clearInterval(self, e):
        self._remove(e)

    def clearTimeout(self, e):
        self._remove(e)

    def schedule(self):
        self._schedule(None)
        if not self.next is None:
            try:
                self.next.action(*self.next.arg)
            except Exception as e:
                print("{} -- {}".format(type(e).__name__, e))
            return True
        else:
            return False

    def run(self):
        while True:
            while self.schedule():
                pass
            machine.idle()
