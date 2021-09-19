from dataclasses import dataclass
from typing import Any, List


@dataclass
class CustomUniverseModel:
    createdAt: str
    date: str
    description: str
    locked: bool
    sids: List[str]
    title: str
    type: str
    updatedAt: str
    userId: str
    watchlistId: Any
    __v: int
    _id: str
