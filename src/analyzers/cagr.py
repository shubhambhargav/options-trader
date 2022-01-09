from datetime import date

from src.apps.console.controllers.tradebook import TradebookController
from src.apps.kite.controllers.holdings import HoldingsController


class CAGRController:
    @staticmethod
    def get_kite_cagr(from_date: date, to_date: date):
        trades = TradebookController.get_trades(segment='EQ', from_date=from_date, to_date=to_date)
        holdings = HoldingsController.get_holdings()

        temp_holdings_dict = {}

        for trade in trades:
            pass
