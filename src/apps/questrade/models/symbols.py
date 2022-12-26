from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import config


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
    eps: float
    pe: float
    dividend: float
    # The following field level aliasing did not work for `from_dict` method in dacite
    # TODO: Figure out the why and fix it
    yield_value: Optional[float] = field(metadata=config(field_name='yield'))
    exDate: str
    marketCap: int
    tradeUnit: int
    optionType: Optional[str]
    optionDurationType: Optional[str]
    optionRoot: str
    optionContractDeliverables: dict
    optionExerciseType: Optional[str]
    listingExchange: str
    description: str
    securityType: str
    optionExpiryDate: Optional[str]
    dividendDate: str
    optionStrikePrice: Optional[str]
    isTradable: bool
    isQuotable: bool
    hasOptions: bool
    currency: str
    minTicks: list
    industrySector: str
    industryGroup: str
    industrySubgroup: str
