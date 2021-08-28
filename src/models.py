from dataclasses import dataclass


@dataclass
class Instrument:
    instrument_token: int
    close_price: float
    last_price: float


@dataclass
class StockOfInterest:
    ticker: str

    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)


@dataclass
class Option:
    tradingsymbol: str
    last_price: float


@dataclass
class ProcessedOption(Option):
    "Option with added metadata for recommendation and selection purposes"
    sequence_id: int
    backup_money: float


@dataclass
class ProcessedOptions(ProcessedOption):
    "This is more of a dataframe representation of Option as compared to an array of objects"
    pass
