from dataclasses import dataclass


@dataclass
class CandleModel:
    start: str
    end: str
    low: float
    high: float
    open: float
    close: float
    volume: int
