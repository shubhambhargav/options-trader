from dataclasses import dataclass
from typing import Any


@dataclass
class InstrumentModel:
    tickersymbol: str
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
    sector: Any


@dataclass
class CandleModel:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
