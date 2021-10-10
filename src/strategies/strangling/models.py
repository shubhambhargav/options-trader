from dataclasses import dataclass
from typing import List


@dataclass
class ConfigModel:
    tickersymbol: str
    validity_in_days: int
    strangle_width: float
