from machine import Pin,Timer
from scheduler import Event
from time import ticks_ms, ticks_diff
import esp

PRESSED = 0
CLICK = 1
LONG_PRESS = 2
DOUBLE_CLICK = 3

class Switch(Event):
    def __init__(self, p, long_press=800, double_click=400, debounce_ms=50):
        super().__init__()
        self.pin = Pin(p, Pin.IN, Pin.PULL_UP)
        self.pressed_at = None
        self.last_change = 0
        self.last_edge = ticks_ms()
        self.long_press = long_press
        self.double_click = double_click
        self.debounce_ms = debounce_ms
        self.clicked = None
        self.pin.irq(self.handler, Pin.IRQ_FALLING | Pin.IRQ_RISING)
        esp32.wake_on_gpio([self.pin],esp32.WAKEUP_ALL_LOW)
        self.timer = Timer(0)

    def siglong_press(self, t):
        self.clicked = None
        self.signal(LONG_PRESS)

    def handler(self, q):
        now = ticks_ms()
        if ticks_diff(now, self.last_edge) < self.debounce_ms:
            return
        self.last_edge = now
        v = self.pin.value()
        if v == PRESSED:
            self.pressed_at = now
            self.timer.init(period=self.long_press, mode=Timer.ONE_SHOT, callback=self.siglong_press)
            self.irq_signal(PRESSED)
        else:
            if self.pressed_at is not None and ticks_diff(now, self.pressed_at) < self.long_press:
                self.timer.deinit()
                if self.clicked is None:
                    self.clicked = now
                    self.irq_signal(CLICK)
                elif ticks_diff(now, self.clicked) <= self.double_click:
                    self.clicked = None
                    self.irq_signal(DOUBLE_CLICK)
                else:
                    self.clicked = now
                    self.irq_signal(CLICK)
            else:
                pass
            self.pressed_at = None
 
