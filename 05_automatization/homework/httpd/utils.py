from datetime import datetime

WEEKDAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


def httpdate():
    """Return a string representation of a date according to RFC 1123
    (HTTP/1.1).

    """
    dt = datetime.utcnow()
    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (WEEKDAYS[dt.month - 1], dt.day, MONTHS[dt.month - 1],
                                                    dt.year, dt.hour, dt.minute, dt.second)
