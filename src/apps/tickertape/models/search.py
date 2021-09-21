from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResponseItem:
    marketCap: float
    match: str
    name: str
    quote: dict
    sector: str
    sid: str
    slug: str
    ticker: str
    type: str
