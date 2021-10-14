from dataclasses import asdict
from PyInquirer import Token, style_from_dict, prompt

from dacite import from_dict

from src.apps.kite.controllers.holdings import HoldingsController
from src.apps.kite.controllers.gtt import GTTController
from src.apps.tickertape.controllers.screens import ScreensController
from src.apps.tickertape.controllers.custom_universes import CustomUniversesController
from src.apps.tickertape.controllers.search import SearchController
from src.apps.tickertape.models.search import StockSidModel
from src.strategies.value_investing.models import ConfigModel

from src.logger import LOGGER

STYLE = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})


class ValueInvestor:
    def __init__(self):
        pass

    def get_config(self) -> ConfigModel:
        screens = ScreensController.list_screens()
        custom_universes = CustomUniversesController.list_custom_universes()

        questions = [
            {
                'type': 'list',
                'name': 'tickertape_screen',
                'message': 'Screen to be loaded',
                'choices': [{ 'name': screen.title, 'value': screen } for screen in screens]
            },
            {
                'type': 'list',
                'name': 'purchased_stocks_universe',
                'message': 'Purchased stocks universe from Tickertape',
                'choices': [{ 'name': custom_universe.title, 'value': custom_universe } for custom_universe in custom_universes]
            }
        ]

        config = prompt(questions=questions, style=STYLE)

        config['tickertape_screen'] = asdict(config['tickertape_screen'])
        config['purchased_stocks_universe'] = asdict(config['purchased_stocks_universe'])

        return from_dict(data_class=ConfigModel, data=config)

    def hedge_stock(self, stock: StockSidModel):
        holding = HoldingsController.get_holding(tradingsymbol=stock.info.ticker)

        if not holding:
            LOGGER.info('No holding found for value stock: %s' % stock.info.ticker)

            return

        gtts = GTTController.get_gtts(tickersymbol=stock.info.ticker)

        if len(gtts) > 1:
            raise ValueError('Expected there to be only 1 GTT, found: %d' % len(gtts))

    def run(self):
        config = self.get_config()

        purchased_value_stocks = SearchController.find_stocks(sids=config.purchased_stocks_universe.sids)

        for stock in purchased_value_stocks:
            self.hedge_stock(stock=stock)
