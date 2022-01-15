from dataclasses import dataclass

from src.constants import ZerodhaEquityTransactionCharges


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

    @property
    def expected_transaction_charges(self):
        buy_charges = self.average_price * self.quantity * (
            ZerodhaEquityTransactionCharges.STT +
            ZerodhaEquityTransactionCharges.TRANSACTION_CHARGES * (1 + ZerodhaEquityTransactionCharges.GST / 100) +
            ZerodhaEquityTransactionCharges.SEBI +
            ZerodhaEquityTransactionCharges.STAMP_CHARGES
        ) / 100

        sell_charges = self.last_price * self.quantity * (
            ZerodhaEquityTransactionCharges.STT +
            ZerodhaEquityTransactionCharges.TRANSACTION_CHARGES * (1 + ZerodhaEquityTransactionCharges.GST / 100) +
            ZerodhaEquityTransactionCharges.SEBI
        ) / 100

        return buy_charges + sell_charges

