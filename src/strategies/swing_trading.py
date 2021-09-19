from src.apps.kite.controllers import HoldingsController
from src.apps.tickertape.controllers import ScreensController


class SwingTradeManager:
    def __init__(self):
        self.holdings = HoldingsController.get_holdings()

    def evaluate(self):
        for holding in self.holdings:
            print(holding)

        screen_data = ScreensController.load_screen(screen_id='YUQEvEqw3Y3btwWe')

        print(screen_data)

    def compare(self):
        pass
