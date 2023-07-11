from time import sleep_ms
import network
from config import NETWORKS


def getNetwork(wlan):
    accpts = wlan.scan()
    for a in accpts:
        name = str(a[0], "UTF-8")
        for n in NETWORKS.keys():
            if n == name:
                return n
    return "notfound"


def do_connected_action(action, status, progress):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    status.update("Scanning")
    mynet = getNetwork(wlan)
    if mynet == "notfound":
        status.update(mynet)
        wlan.active(False)
        return
    count = 0
    if not wlan.isconnected():
        status.update(mynet)
        wlan.connect(mynet, NETWORKS[mynet])
        while not wlan.isconnected():
            sleep_ms(1000)
            progress.update(str(count))
            count += 1
            if count > 15:
                status.update("Failed")
                wlan.active(False)
                return
    status.update("Connected")
    progress.update("")
    sleep_ms(1000)
    try:
        action()
        status.update("Done")
    except Exception as e:
        status.update("Failed " + str(e))
    wlan.active(False)
