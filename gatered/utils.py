from datetime import datetime


def get_timestamp(dt: datetime):
    return int(dt.replace(microsecond=0).timestamp())
