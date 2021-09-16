from dataclasses import dataclass


@dataclass
class PositionModel:
    average_price: float
    buy_m2m: float
    buy_price: float
    buy_quantity: int
    buy_value: float
    close_price: int
    day_buy_price: float
    day_buy_quantity: int
    day_buy_value: float
    day_sell_price: float
    day_sell_quantity: int
    day_sell_value: float
    exchange: str
    instrument_token: int
    last_price: float
    m2m: float
    multiplier: int
    overnight_quantity: int
    pnl: float
    product: str
    quantity: int
    sell_m2m: float
    sell_price: float
    sell_quantity: int
    sell_value: float
    realised: float
    tradingsymbol: str
    unrealised: float
    value: float

    @property
    def pnl_month_end(self) -> float:
        # TODO: Add logic for CE type options as well
        if self.tradingsymbol.endswith('PE') and self.quantity < 0:
            return abs(self.quantity * self.average_price)

        return self.pnl

