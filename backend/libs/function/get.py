import datetime

flag = datetime.datetime(2002, 2, 26)


def getDate():
    current = datetime.datetime.now()
    return (current - flag).days

