from dataclasses import dataclass, field
from typing import Any, Optional, Union

from dataclasses_json import config, dataclass_json

from .base import StockOfInterest


@dataclass_json
@dataclass
class InstrumentModel:
    tickersymbol: str
    # The following field level aliasing did not work for `from_dict` method in dacite
    # TODO: Figure out the why and fix it
    volume_200DMA: Optional[float] = field(metadata=config(field_name='200DMA_volume'))
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


@dataclass
class EnrichedInstrumentModel(StockOfInterest):
    last_buy_signal: Any = ''
    macd: float = 0
    rsi: float = 0
    close_last_by_min: float = 0
    close_last_by_avg: float = 0
    last_support: Union[float, None] = 0
    last_resistance: Union[float, None] = 0
    close_last_by_support: Union[float, None] = 0
    close_last_by_resistance: Union[float, None] = 0
