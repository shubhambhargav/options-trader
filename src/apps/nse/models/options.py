from dataclasses import dataclass


@dataclass
class HistoricalOptionModel:
    symbol: str
    date: str
    expiry: str
    option_type: str
    strike_price: str
    open: str
    high: str
    low: str
    close: str
    ltp: str
    settle_price: str
    no_of_contracts: str
    turnover_in_lacs: str
    premium_turnover_in_lacs: str
    open_int: str
    change_in_oi: str
    underlying_value: str
