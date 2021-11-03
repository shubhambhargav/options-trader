from dataclasses import MISSING, dataclass, field
from typing import List, Optional


@dataclass
class OrderModel:
    average_price: float
    cancelled_quantity: int
    disclosed_quantity: int
    exchange: str
    exchange_order_id: str
    exchange_timestamp: str
    exchange_update_timestamp: str
    filled_quantity: int
    guid: Optional[str]
    instrument_token: int
    market_protection: int
    meta: dict
    order_id: str
    order_timestamp: str
    order_type: str
    parent_order_id: Optional[str]
    pending_quantity: int
    placed_by: str
    price: float
    product: str
    quantity: int
    status: str
    status_message = Optional[str]
    status_message_raw: Optional[str]
    tag: Optional[str]
    tradingsymbol: str
    transaction_type: str
    trigger_price: float
    validity: str
    variety: str
    tags: List[str] = field(default=list)
    is_open: bool = False

    def __post_init__(self):
        if self.status == 'OPEN':
            self.is_open = True


@dataclass
class PlaceOrderModel:
    tradingsymbol: str
    transaction_type: str
    quantity: int
    price: float
    user_id: str = ''
    order_type: str = 'LIMIT'
    product: str = 'NRML'
    validity: str = 'DAY'
    variety: str = 'regular'
    exchange: str = 'NFO'
    disclosed_quantity: int = 0
    trigger_price: float = 0
    squareoff: float = 0
    stoploss: float = 0
    trailing_stoploss: float = 0

