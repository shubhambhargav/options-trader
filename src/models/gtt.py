from dataclasses import dataclass, is_dataclass
from typing import Any, List


@dataclass
class OrderModel:
    price: float
    quantity: int
    tradingsymbol: str
    transaction_type: str
    exchange: str = 'NFO'
    order_type: str = 'LIMIT'
    product: str = 'NRML'
    result: Any = None


@dataclass
class ConditionModel:
    last_price: float
    tradingsymbol: str
    trigger_values: List[float]
    exchange: str = 'NFO'
    instrument_token: int = None


@dataclass
class GTTModel:
    condition: ConditionModel
    orders: List[OrderModel]
    expires_at: str
    user_id: str = None
    id: int = None
    created_at: str = None
    updated_at: str = None
    parent_trigger: Any = None
    status: str = 'active'
    type: str = 'single'
