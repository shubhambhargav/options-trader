from dataclasses import dataclass, field


@dataclass
class HistoricalOptionModel:
    symbol: str
    date: str
    expiry: str
    option_type: str
    strike_price: float
    open: float
    high: float
    low: float
    close: float
    ltp: float
    settle_price: float
    no_of_contracts: str
    turnover_in_lacs: str
    premium_turnover_in_lacs: str
    open_int: str
    change_in_oi: str
    underlying_value: str
