from dataclasses import dataclass, is_dataclass, field
from typing import Any, List
from datetime import datetime

from .base import DefaultVal
from .instruments import InstrumentModel
from .positions import PositionModel

OPTIONS_EXPIRY_DATETIME_FORMAT = '%Y-%m-%d'


@dataclass
class OptionModel:
    broker: str
    exchange: str
    expiry: str
    instrument_token: int
    instrument_type: str
    is_non_fno: bool
    is_underlying: bool
    last_price: float
    last_quantity: int
    last_traded_timestamp: int
    last_updated_at: str
    lot_size: float
    mode: str
    multiplier: float
    name: str
    oi: int
    segment: str
    strike: float
    tick_size: float
    tradable: bool
    tradingsymbol: str
    underlying_instrument: str
    volume: int
    backup_money: float = 0
    profit: float = 0
    time_to_expiry_in_days: int = 0

    def __post_init__(self):
        self.backup_money = self.strike * self.lot_size
        self.profit = self.last_price * self.lot_size
        self.time_to_expiry_in_days = (
            datetime.strptime(self.expiry, OPTIONS_EXPIRY_DATETIME_FORMAT) - datetime.now()
        ).days


@dataclass
class OptionMarginModel:
    total: float
    type: str
    tradingsymbol: str
    exchange: str
    span: float
    exposure: float
    option_premium: float
    additional: float
    bo: float
    cash: float
    var: float
    pnl: dict
    total: float


@dataclass
class EnrichedOptionModel(OptionModel):
    "Option with added metadata for recommendation and selection purposes"
    percentage_dip: float = 0
    margin: OptionMarginModel = DefaultVal(OptionMarginModel)
    instrument_data: InstrumentModel = DefaultVal(InstrumentModel)
    sequence_id: int = 0
    profit__percentage: float = 0
    position: PositionModel = DefaultVal(PositionModel)
    instrument_positions: List[PositionModel] = DefaultVal(List[PositionModel])
