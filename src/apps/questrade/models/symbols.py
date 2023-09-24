from dataclasses import dataclass, field
from typing import Optional, Union, Any

from dataclasses_json import config


@dataclass
class SymbolBaseModel:
    symbol: str
    symbolId: int


@dataclass
class SymbolModel:
    symbol: str
    symbolId: int
    prevDayClosePrice: float
    highPrice52: float
    lowPrice52: float
    averageVol3Months: int
    averageVol20Days: int
    outstandingShares: int
    eps: Optional[float]
    pe: Optional[float]
    dividend: Optional[float]
    # The following field level aliasing did not work for `from_dict` method in dacite
    # TODO: Figure out the why and fix it
    yield_value: Optional[float] = field(metadata=config(field_name='yield'))
    exDate: Optional[str]
    marketCap: int
    tradeUnit: Optional[int]
    optionType: Optional[str]
    optionDurationType: Optional[str]
    optionRoot: Optional[str]
    optionContractDeliverables: dict
    optionExerciseType: Optional[str]
    listingExchange: str
    description: str
    securityType: str
    optionExpiryDate: Optional[str]
    dividendDate: Optional[str]
    optionStrikePrice: Optional[str]
    isTradable: bool
    isQuotable: bool
    hasOptions: bool
    currency: str
    minTicks: list
    industrySector: str
    industryGroup: str
    industrySubgroup: str


@dataclass
class EnrichedSymbolModel:
    symbol: str
    last_buy_signal: Any = ''
    macd: float = 0
    rsi: float = 0
    close_last_by_min: float = 0
    close_last_by_avg: float = 0
    last_support: Union[float, None] = 0
    last_resistance: Union[float, None] = 0
    close_last_by_support: Union[float, None] = 0
    close_last_by_resistance: Union[float, None] = 0
