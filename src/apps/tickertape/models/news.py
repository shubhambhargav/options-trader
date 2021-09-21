from dataclasses import dataclass
from typing import List


@dataclass
class NewsModel:
    date: str
    description: str
    feed_type: str
    image: str
    link: str
    publisher: dict
    stocks: List[dict]
    title: str
    _id: str
