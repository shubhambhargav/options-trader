from dataclasses import dataclass
from typing import Any, Optional, List, Union


@dataclass
class UserModel:
    avatar_url: Optional[str]
    bank_accounts: List[Any]
    broker: str
    dp_ids: List[str]
    email: str
    exchanges: List[str]
    meta: dict
    order_types: List[str]
    pan: str
    password_timestamp: str
    phone: str
    products: List[str]
    tags: List[Any]
    twofa_timestamp: str
    twofa_type: str
    user_id: str
    user_name: str
    user_shortname: str
    user_type: str


@dataclass
class AvailableMarginModel:
    adhoc_margin: Union[int, float]
    cash: Union[int, float]
    collateral: Union[int, float]
    intraday_payin: Union[int, float]
    live_balance: Union[int, float]
    opening_balance: Union[int, float]


@dataclass
class UtilisedMarginModel:
    debits: Union[int, float]
    delivery: Union[int, float]
    exposure: Union[int, float]
    holding_sales: Union[int, float]
    liquid_collateral: Union[int, float]
    m2m_realised: Union[int, float]
    m2m_unrealised: Union[int, float]
    option_premium: Union[int, float]
    payout: Union[int, float]
    span: Union[int, float]
    stock_collateral: Union[int, float]
    turnover: Union[int, float]


@dataclass
class EquityMarginModel:
    available: AvailableMarginModel
    enabled: bool
    net: Union[int, float]
    utilised: UtilisedMarginModel


@dataclass
class MarginsModel:
    commodity: dict
    equity: EquityMarginModel
