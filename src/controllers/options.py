import requests

from .instruments import InstumentsController

from ..models import (
    ProcessedOption as ProcessedOptionModel,
    Instrument as InstrumentModel
)
from .._variables import VARIABLES
from .. import utilities as Utilities


class OptionsController:
    def __init__(self):
        self.option_chain = {}

    def get_option_last_price(self, option: ProcessedOptionModel):
        # TODO: Find a better way to get the last price. Currently we are getting
        #       the entire option chain to get the last price of an option
        option_chain = InstumentsController.get_options_chain(instrument=InstrumentModel(**option.instrument_data))

        for option in option_chain:
            if option['tradingsymbol'] == option.tradingsymbol:
                return option['last_price']

        return None

    def sell_option(self, option: ProcessedOptionModel):
        # Since the price of the option can change during the analysis,
        # following code ensures that we don't trade at a lower value than the last price
        if not isinstance(option, ProcessedOptionModel):
            option = ProcessedOptionModel(**option)

        option_last_price = self.get_option_last_price(tradingsymbol=self.name, underlying_instrument=option['instrument'])
        expected_trade_price = self.last_price

        if option_last_price > expected_trade_price:
            print(
                'Increasing the trade price for %s. Previous price: %s, new price: %s' % (
                    self.name, expected_trade_price, option_last_price
                )
            )
            print('New expected profit: %s' % (expected_trade_price * int(self.lot_size)))

            expected_trade_price = option_last_price

        data = {
            'variety': 'regular',
            'exchange': 'NFO',
            'tradingsymbol': self.name,
            'transaction_type': 'SELL',
            'order_type': 'LIMIT',
            'quantity': int(self.lot_size),
            'price': Utilities.round_nearest(number=expected_trade_price + 0.09, unit=0.05),
            'product': 'NRML',
            'validity': 'DAY',
            'disclosed_quantity': '0',
            'trigger_price': '0',
            'squareoff': '0',
            'stoploss': '0',
            'trailing_stoploss': '0',
            'user_id': VARIABLES.CONFIG['user_id'],
            'gtt_params': '[[0,%s],[0,%s]]' % (VARIABLES.TARGET, VARIABLES.STOPLOSS)
        }

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
        }
        
        response = requests.post(
            'https://kite.zerodha.com/oms/orders/regular',
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            print('Successfully placed the order for %s' % self.name)
            
            return

        print('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))
