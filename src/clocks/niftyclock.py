from micropython import const
from tempos import g,rtc,sched
from graphics import rgb,WHITE,BLACK,BLUE,CYAN,RED
from fonts import hugefont,roboto24

X = const(35)

days = ["Mon","Tues","Wed","Thu","Fri","Sat","Sun"]
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def drawTime():
    t=rtc.datetime()
    g.fill(BLACK)
    g.setfont(hugefont)
    g.text("{:02}".format(t[4]),X,40,WHITE)
    g.text("{:02}".format(t[5]),X,130,WHITE)
    g.fill_rect(X+110,40,4,162,CYAN)
    g.setfont(roboto24)
    g.text(str(t[0]),X+124,40,WHITE)
    g.text("{:02}".format(t[1]),X+124,64,WHITE)
    g.text("{:02}".format(t[2]),X+124,88,WHITE)
    g.text(months[t[1]-1],X+124,154,WHITE)
    g.text(days[t[3]],X+124,178,WHITE)
    g.show()

ticker = None

def app_init():
    global ticker
    drawTime()
    ticker = sched.setInterval(10000,drawTime)
    
def app_end():
    sched.clearInterval(ticker)
    g.fill(BLACK)



