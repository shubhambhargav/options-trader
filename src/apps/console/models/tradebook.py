from dataclasses import dataclass
from typing import Union


@dataclass
class Trade:
    exchange: str
    expiry_date: str
    external_trade_type: str
    instrument_id: str
    instrument_type: str
    isin: str
    order_execution_time: str
    order_id: str
    price: Union[int, float]
    quantity: int
    segment: str
    series: str
    strike: int
    tag_ids: Union[str, None]
    trade_date: str
    trade_id: str
    trade_type: str
    tradingsymbol: str
