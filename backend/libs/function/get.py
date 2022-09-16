import datetime

flag = datetime.datetime(2002, 2, 26)


def getDate():
    current = datetime.datetime.now()
    return (current - flag).days


def getOrder(ordering: str):
    desc = ""
    if ordering.startswith("-"):
        ordering = ordering[1:]
        desc = "DESC"
    return {"order": ordering, "desc": desc}
