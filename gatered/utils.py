from datetime import datetime


def get_timestamp(dt: datetime):
    """Transform `datetime` to Epoch timestamp as `int`."""
    return int(dt.replace(microsecond=0).timestamp())
