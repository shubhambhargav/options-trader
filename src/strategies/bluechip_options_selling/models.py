from dataclasses import dataclass
from typing import List, Union

from src.apps.kite.models import StockOfInterest


@dataclass
class ConfigModel:
    is_order_enabled: bool
    is_order_profit_booking_enabled: bool
    stocks: List[StockOfInterest]


@dataclass
class BackTestConfigModel:
    entry_day_before_expiry_in_days: int = 3
    last_n_iterations: Union[int, None] = 3
    filter_stocks_by_technicals: bool = True
    entry_point_from_last_support: int = 30  # in percentage points
