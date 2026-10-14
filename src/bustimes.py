import ure
import time
import requests
import time
import math

def parseDateTime(datestr):
    regex = "^(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z$"
    match = ure.match(regex, datestr)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        seconds = int(match.group(6))
        return time.mktime((year, month, day, hour, minute, seconds,0,0))
    else:
        return None
    
    
def getdelay(ts):
    at = parseDateTime(ts)
    if at is None:
        return None
    secs = at + 3600 - time.time()
    return int(secs/60)


def bustimes(naptanId):
    URL = "https://api.tfl.gov.uk/StopPoint/{}/Arrivals".format(naptanId)
    r = requests.get(URL)       
    dd = r.json()
    for e in dd:
        line = e["lineName"]
        arrival = e["expectedArrival"]
        print(line," ",arrival," ",getdelay(arrival))
        
import wifi
wifi.connect()
bustimes("490009652N")

   