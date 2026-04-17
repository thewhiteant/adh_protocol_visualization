import datetime

def timenow():
    return str(datetime.datetime.now().strftime("%M%m%d%y%M%d%M%M"))

def timecheck(check_time):
    return str(timenow()) == str(check_time)
