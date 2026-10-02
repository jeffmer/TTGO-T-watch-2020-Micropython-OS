# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from machine import Pin, soft_reset
import esp32

def onpress(t):
    global bat
    bat.value(0)

lcdrst=Pin(40, Pin.OUT, value=1)
bat = Pin(2,Pin.OUT,value=1)
pwr = Pin(5,Pin.IN)
pwr.irq(onpress, Pin.IRQ_FALLING)

def onplus(t):
    global sched
    pass
#    sched.stop()
    
plus = Pin(4,Pin.IN)
plus.irq(onplus, Pin.IRQ_FALLING)
esp32.wake_on_gpio([plus],esp32.WAKEUP_ALL_LOW)

if not plus.value() == 0:
    import loader


    