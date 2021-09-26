from dataclasses import dataclass
from typing import List


@dataclass
class ConfigModel:
    tickers: List[str]
