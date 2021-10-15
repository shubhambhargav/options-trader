from dataclasses import dataclass
from typing import List


@dataclass
class ConfigModel:
    tickersymbol: str
    validity_in_days: int
    strangle_width: float


@dataclass
class ConfigV2Model:
    tickersymbol: str
    strangle_gap: int
    stoploss_pnl: int
    is_mock_run: bool


@dataclass
class MockPositionModel:
    tradingsymbol: str
    instrument_token: int
    pnl: float
