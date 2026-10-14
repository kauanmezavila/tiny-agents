from datetime import datetime

def compareDates(date1: str, date2: str) -> int:
    d1 = datetime.fromisoformat(date1)
    d2 = datetime.fromisoformat(date2)
    if d1 < d2:
        return -1
    elif d1 > d2:
        return 1
    return 0