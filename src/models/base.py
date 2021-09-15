from dataclasses import dataclass, is_dataclass, field
from typing import Any


@dataclass
class DefaultVal:
    val: Any


@dataclass
class Instrument:
    instrument_token: int
    close_price: float
    net_change: float
    last_price: float
    volume: int
    prev_day_volume: int
    prev_day_traded_value: float
    projected_volume: int
    last_updated_at: str
    per_expiry_data: dict
    sector: str


@dataclass
class StockCustomFilters:
    minimum_dip: float = 5
    maximum_dip: float = 20


@dataclass
class StockOfInterest:
    ticker: str
    custom_filters: StockCustomFilters = field(default_factory=StockCustomFilters, init=True)
