from dataclasses import dataclass
from typing import List, Union, Optional

from src.apps.kite.models import StockOfInterest


@dataclass
class AutomationConfig:
    filter_stocks_by_technicals: bool = True
    filter_options_by_open_int: bool = True
    filter_options_min_percentage_dip: float = 10
    filter_options_max_percentage_dip: float = 16
    filter_options_min_profit: float = 2000
    filter_options_max_profit: float = 15000
    filter_options_min_open_int: float = 0
    entry_point_from_last_support: int = 50  # in percentage points


@dataclass
class ConfigModel:
    is_order_enabled: bool
    is_order_profit_booking_enabled: bool
    stocks: List[StockOfInterest]
    automation_config: Optional[AutomationConfig]
    is_automated: bool = False


@dataclass
class BackTestConfigModel(AutomationConfig):
    available_margin: int = 1000000  # 10 lakhs
    entry_day_before_expiry_in_days: int = 25
    last_n_iterations: Union[int, None] = 3
