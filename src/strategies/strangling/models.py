from dataclasses import dataclass
from typing import List


@dataclass
class ConfigModel:
    tickersymbol: str
    validity_in_days: int
    strangle_width: float


@dataclass
class ConfigV2Model:
    tickersymbol: str = 'NIFTY'
    strangle_gap: int = 200
    stoploss_pnl: int = -1000
    is_mock_run: bool = False
    is_backtest: bool = False


@dataclass
class MockPositionModel:
    tradingsymbol: str
    average_price: float
    quantity: float
    instrument_token: int
    pnl: float
