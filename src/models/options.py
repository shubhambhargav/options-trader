from dataclasses import dataclass, is_dataclass, field
from typing import Any

import requests

from .base import DefaultVal, Instrument


@dataclass
class Option:
    broker: str
    exchange: str
    expiry: str
    instrument_token: str
    instrument_type: str
    is_non_fno: bool
    is_underlying: bool
    last_price: float
    last_quantity: int
    last_traded_timestamp: int
    last_updated_at: str
    lot_size: int
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


@dataclass
class OptionMargin:
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
class OptionProfit:
    value: float
    percentage: float


@dataclass
class ProcessedOption(Option):
    "Option with added metadata for recommendation and selection purposes"
    percentage_dip: float = DefaultVal(0)
    margin: OptionMargin = DefaultVal(OptionMargin)
    profit: OptionProfit = DefaultVal(OptionProfit)
    instrument_data: Instrument = DefaultVal(Instrument)
    backup_money: float = DefaultVal(0)
    sequence_id: int = DefaultVal(0)

    @property
    def __dict__(self):
        dict_data = super(ProcessedOption, self).__dict__

        for key, value in dict_data.items():
            if is_dataclass(value):
                dict_data[key] = value.__dict__

        return dict_data


@dataclass
class ProcessedOptions(ProcessedOption):
    "This is more of a dataframe representation of Option as compared to an array of objects"
    pass
