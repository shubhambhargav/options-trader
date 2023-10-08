from dataclasses import dataclass
from typing import Union, Optional


@dataclass
class SymbolModel:
    symbol: str
    long_mr: int
    short_mr: int
    intrinsic_value: Union[float, str]
    percentage: Optional[float]
    is_active: bool
