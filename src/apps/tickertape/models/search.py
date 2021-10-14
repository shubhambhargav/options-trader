from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResponseItem:
    marketCap: Optional[float]
    match: str
    name: str
    quote: dict
    sector: str
    sid: str
    slug: str
    ticker: str
    type: str


@dataclass
class StockInfoModel:
    exchange: str
    name: str
    sector: str
    slug: str
    ticker: str
    tradable: bool
    type: str


@dataclass
class StockSidModel:
    info: StockInfoModel
    sid: str
