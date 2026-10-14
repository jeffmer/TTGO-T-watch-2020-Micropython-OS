from time import sleep_ms
import network
from config import SSID,PWD
from temopos import sched

_wlan = network.WLAN(network.STA_IF)
_lazyTO = None


def connect(status=None, progress=None):
    global _lazyTO
    "Connect wlan to the configured network. Returns True on success."
    if _wlan.isconnected():
        if not _lazyTO is None:
            sched.clearTimeout(_lazyTO)
            _lazyTO = None
        return True
    output = status.update if status else print
    _wlan.active(True)
    output("Connecting")
    count = 0
    if not _wlan.isconnected():
        output(SSID)
        _wlan.connect(SSID, PWD)
        while not _wlan.isconnected():
            sleep_ms(1000)
            if progress:
                progress.update(str(count))
            count += 1
            if count > 15:
                output("Failed")
                _wlan.active(False)
                return False
    output("Connected")
    if progress:
        progress.update("")
    return True


def disconnect():
    global _lazyTO
    _wlan.active(False)
    _lazyTO = None

def lazy_disconnect():
    global _lazyTO
    _lazyTO = sched.setTimeout(10000,disconnect)


def do_connected(action, status=None, progress=None):
    "execute fn 'action' on an established connection. Write output to status Label, or print if None."
    output = status.update if status else print
    try:
        action()
        output("Done")
    except Exception as e:
        output("Failed " + str(e))


def do_connected_action(action, status=None, progress=None):
    if not connect(status, progress):
        return
    do_connected(action, status, progress)
    lazy_disconnect()
