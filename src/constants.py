from dataclasses import dataclass
from datetime import date
from typing import Dict

from dacite import from_dict


@dataclass
class HolidayAlernateModel:
    option_expiry: date


MARKET_HOLIDAYS_ALTERNATES: Dict[date, HolidayAlernateModel] = {
    date(2021, 10, 15): from_dict(
        data_class=HolidayAlernateModel,
        data={
            'option_expiry': date(2021, 10, 14)
        }
    )
}
