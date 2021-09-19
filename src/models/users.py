from dataclasses import dataclass
from typing import Any, Optional, List


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
