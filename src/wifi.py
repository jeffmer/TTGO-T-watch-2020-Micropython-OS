from time import sleep_ms
import network
from config import NETWORKS


def getNetwork(wlan):
    "finds which surounding wifi networks can be logged into using the config.py file"
    accpts = wlan.scan()
    for a in accpts:
        name = str(a[0], "UTF-8")
        for n in NETWORKS.keys():
            if n == name:
                return n
    return "notfound"


def do_connected_action(action, status=None, progress=None):
    "connect to internet then execute fn 'action'. Write output to status and progress Labels. If status is None, output will be printed instead."
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if status:
        output = status.update
    else:
        output = print
    output("Scanning")
    mynet = getNetwork(wlan)
    if mynet == "notfound":
        output(mynet)
        wlan.active(False)
        return
    count = 0
    if not wlan.isconnected():
        output(mynet)
        wlan.connect(mynet, NETWORKS[mynet])
        while not wlan.isconnected():
            sleep_ms(1000)
            if progress:
                progress.update(str(count))
            count += 1
            if count > 15:
                output("Failed")
                wlan.active(False)
                return
    output("Connected")
    if progress:
        progress.update("")
    sleep_ms(1000)
    try:
        action()
        output("Done")
    except Exception as e:
        output("Failed " + str(e))
    wlan.active(False)
