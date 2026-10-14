import requests


def getDetail(cs):
    URL = "https://api.adsbdb.com/v0/callsign/{}".format(cs)
    r = requests.get(URL)       
    dd = r.json()
    if dd["response"] == "unknown callsign":
        return (False, "","","")
    else:
        return  (True,
                 dd["response"]["flightroute"]["airline"]["callsign"],
                 dd["response"]["flightroute"]["origin"]["municipality"],
                 dd["response"]["flightroute"]["destination"]["municipality"])
               


