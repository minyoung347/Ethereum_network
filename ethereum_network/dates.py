from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from dateutil.relativedelta import relativedelta


def month_start(month: str) -> datetime:
    return datetime.strptime(month, "%Y%m").replace(tzinfo=timezone.utc)


def next_month(month: str) -> datetime:
    return month_start(month) + relativedelta(months=1)


def month_range(start: str, end: str) -> list[str]:
    months = pd.date_range(start=month_start(start), end=month_start(end), freq="MS")
    return [month.strftime("%Y%m") for month in months]
