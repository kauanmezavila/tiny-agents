from datetime import datetime, timezone


def hourNow():
    return {"utc": datetime.now(timezone.utc).isoformat()}
