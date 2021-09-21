from dataclasses import dataclass


@dataclass
class HoldingModel:
    authorised_date: str
    authorised_quantity: int
    average_price: float
    close_price: float
    collateral_quantity: int
    collateral_type: str
    day_change: float
    day_change_percentage: float
    discrepancy: bool
    exchange: str
    instrument_token: int
    isin: str
    last_price: float
    opening_quantity: int
    pnl: float
    price: float
    product: str
    quantity: int
    realised_quantity: int
    t1_quantity: int
    tradingsymbol: str
    used_quantity: int