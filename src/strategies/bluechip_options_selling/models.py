from dataclasses import dataclass
from typing import List

from src.apps.kite.models import StockOfInterest


@dataclass
class ConfigModel:
    is_order_enabled: bool
    is_order_profit_booking_enabled: bool
    stocks: List[StockOfInterest]


@dataclass
class BackTestConfigModel:
    pass
