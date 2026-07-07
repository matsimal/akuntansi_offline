from datetime import date, timedelta
import calendar

DATE_FORMAT = "%d/%m/%Y"


def today_str(date_format: str = DATE_FORMAT) -> str:
    return date.today().strftime(date_format)


def today() -> date:
    return date.today()


def yesterday() -> date:
    return date.today() - timedelta(days=1)


def start_of_month() -> date:
    today_date = date.today()
    return date(today_date.year, today_date.month, 1)


def end_of_month() -> date:
    today_date = date.today()
    last_day = calendar.monthrange(today_date.year, today_date.month)[1]
    return date(today_date.year, today_date.month, last_day)


def start_of_year() -> date:
    today_date = date.today()
    return date(today_date.year, 1, 1)


def end_of_year() -> date:
    today_date = date.today()
    return date(today_date.year, 12, 31)