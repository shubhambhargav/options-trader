from dataclasses import dataclass, is_dataclass, field
from typing import Any


@dataclass
class DefaultVal:
    val: Any


@dataclass
class StockCustomFilters:
    minimum_dip: float = 5
    maximum_dip: float = 20


@dataclass
class StockOfInterest:
    ticker: str
    custom_filters: StockCustomFilters = field(default_factory=StockCustomFilters, init=True)
