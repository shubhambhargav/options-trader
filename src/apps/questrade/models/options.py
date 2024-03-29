from datetime import datetime
from typing import List, Optional

from dataclasses import dataclass


@dataclass
class OptionFilterModel:
    optionType: str
    underlyingId: int
    expiryDate: datetime
    minStrikePrice: float
    maxStrikePrice: float

    def to_json(self):
        return {
            'optionType': self.optionType,
            'underlyingId': self.underlyingId,
            'expiryDate': self.expiryDate.strftime('%Y-%m-%dT%H:%M:%S.000000-5:00'),
            'minStrikePrice': self.minStrikePrice,
            'maxStrikePrice': self.maxStrikePrice,
        }


@dataclass
class ChainPerStrikePriceModel:
    strikePrice: float
    callSymbolId: int
    putSymbolId: int


@dataclass
class OptionRootModel:
    optionRoot: str
    chainPerStrikePrice: List[ChainPerStrikePriceModel]
    multiplier: int


@dataclass
class OptionModel:
    expiryDate: str
    description: str
    listingExchange: str
    optionExerciseType: str
    chainPerRoot: List[OptionRootModel]


@dataclass
class OptionQuoteModel:
    underlying: str
    underlyingId: int
    symbol: str
    symbolId: int
    bidPrice: Optional[float]
    bidSize: int
    askPrice: Optional[float]
    askSize: int
    lastTradePriceTrHrs: Optional[float]
    lastTradePrice: Optional[float]
    lastTradeSize: Optional[int]
    lastTradeTick: Optional[str]
    lastTradeTime: Optional[str]
    volume: int
    openPrice: float
    highPrice: float
    lowPrice: float
    volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    openInterest: int
    delay: int
    isHalted: bool
    VWAP: float
