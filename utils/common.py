import datetime

def timenow():
    return datetime.datetime.now().strftime("%m%M%H%d%Y")

def timecheck(timestamp):
    return abs((datetime.datetime.now() - timestamp).total_seconds()) <= 5