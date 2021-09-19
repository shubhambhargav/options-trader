from src.apps.kite.controllers import holdings
from src.apps.kite.controllers.holdings import HoldingsController


class SwingTradeManager:
    def __init__(self):
        self.holdings = HoldingsController.get_holdings()

    def evaluate(self):
        for holding in self.holdings:
            print(holding)

    def compare(self):
        pass
