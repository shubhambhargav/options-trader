from dataclasses import dataclass, is_dataclass, field
from typing import Any
from datetime import datetime

from .base import DefaultVal
from .instruments import InstrumentModel

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

    @property
    def time_to_expiry_in_days(self) -> int:
        today = datetime.now()
        expiry = datetime.strptime(self.expiry, OPTIONS_EXPIRY_DATETIME_FORMAT)

        return (expiry - today).days


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
class OptionProfitModel:
    value: float
    percentage: float


@dataclass
class ProcessedOptionModel(OptionModel):
    "Option with added metadata for recommendation and selection purposes"
    percentage_dip: float = DefaultVal(0)
    margin: OptionMarginModel = DefaultVal(OptionMarginModel)
    profit: OptionProfitModel = DefaultVal(OptionProfitModel)
    instrument_data: InstrumentModel = DefaultVal(InstrumentModel)
    backup_money: float = DefaultVal(0)
    sequence_id: int = DefaultVal(0)


@dataclass
class ProcessedOptionsModel(ProcessedOptionModel):
    "This is more of a dataframe representation of Option as compared to an array of objects"
    pass
