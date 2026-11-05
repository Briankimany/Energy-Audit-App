import re
from datetime import date

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def parse_month(value) -> date:
    if not isinstance(value, str):
        raise ValueError("month must be a YYYY-MM string")
    text = value.strip()
    if not MONTH_PATTERN.match(text):
        raise ValueError("month must be YYYY-MM")
    year, month = int(text[:4]), int(text[5:])
    return date(year, month, 1)


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")
