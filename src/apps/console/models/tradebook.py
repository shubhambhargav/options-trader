from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Union

TRADE_TYPE_SELL = 'sell'
TRADE_TYPE_BUY = 'buy'
TRADE_DATE_FORMAT = '%Y-%m-%d'
STRINGIFIED_INTEGERS = tuple([str(elem) for elem in range(0, 10)])


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
    # Computed variables
    trade_date_dt: Optional[date]

    def __post_init__(self):
        self.trade_date_dt = datetime.strptime(self.trade_date, TRADE_DATE_FORMAT).date()

    @property
    def is_gold_bond(self):
        return True if self.tradingsymbol.startswith('SGB') else False

    @property
    def is_external_bond(self):
        return True if self.tradingsymbol.startswith(STRINGIFIED_INTEGERS) else False
