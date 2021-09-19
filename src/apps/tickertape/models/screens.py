from dataclasses import dataclass, field
from typing import Any, List

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class StockAdvancedRatioModel:
    revenue_change_5y: float = field(metadata=config(field_name='5YrevChg'))
    high_to_current_52w: float = field(metadata=config(field_name='52whd'))
    apef: float
    aroi: float
    fundamental: float
    incTrev: float
    lastPrice: float
    mrktCapf: float
    pb_ratio: float = field(metadata=config(field_name='pbr'))
    sub_industry: str


@dataclass
class StockInfoModel:
    name: str
    sector: str
    ticker: str


@dataclass
class StockModel:
    advancedRatios: StockAdvancedRatioModel
    info: StockInfoModel


@dataclass
class StockResultModel:
    sid: str
    stocl: StockModel


@dataclass
class ScreenedStocksModel:
    results: List[StockResultModel]
    stats: dict


@dataclass
class ScreenModel:
    config: dict
    filters: List[dict]
    isAccessRestricted: bool
    screened: dict
    universes: List[Any]
