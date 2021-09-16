import json
from typing import List
from dacite.core import from_dict

import requests

from .instruments import InstrumentsController

from ..models import (
    OptionModel,
    OptionMarginModel,
    ProcessedOptionModel,
    InstrumentModel
)
from .._variables import VARIABLES
from .. import utilities as Utilities


class OptionsController:
    @staticmethod
    def get_option_last_price(option: ProcessedOptionModel) -> float:
        if not isinstance(option, ProcessedOptionModel):
            option = from_dict(data_class=ProcessedOptionModel, data=option)

        # TODO: Find a better way to get the last price. Currently we are getting
        #       the entire option chain to get the last price of an option
        option_chain = InstrumentsController.get_options_chain(instrument=InstrumentModel(**option.instrument_data))

        for option in option_chain:
            if option['tradingsymbol'] == option.tradingsymbol:
                return option['last_price']

        return None

    @staticmethod
    def sell_option(option: ProcessedOptionModel):
        # Since the price of the option can change during the analysis,
        # following code ensures that we don't trade at a lower value than the last price
        if not isinstance(option, ProcessedOptionModel):
            option = ProcessedOptionModel(**option)

        option_last_price = OptionsController.get_option_last_price(tradingsymbol=option.name, underlying_instrument=option['instrument'])
        expected_trade_price = option.last_price

        if option_last_price > expected_trade_price:
            print(
                'Increasing the trade price for %s. Previous price: %s, new price: %s' % (
                    option.name, expected_trade_price, option_last_price
                )
            )
            print('New expected profit: %s' % (expected_trade_price * int(option.lot_size)))

            expected_trade_price = option_last_price

        data = {
            'variety': 'regular',
            'exchange': 'NFO',
            'tradingsymbol': option.name,
            'transaction_type': 'SELL',
            'order_type': 'LIMIT',
            'quantity': int(option.lot_size),
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
            print('Successfully placed the order for %s' % option.name)

            return

        print('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))

    @staticmethod
    def get_option_margin_bulk(options: List[OptionModel]) -> List[OptionMarginModel]:
        # Note: Hard-coded for options and SELL type for now
        # TODO: Possibly change to leverage BUY as well
        data = []
        chunk_size = 100
        return_data = []

        for option in options:
            data.append({
                'exchange': 'NFO',
                'tradingsymbol': option.tradingsymbol,
                'transaction_type': 'SELL',
                'product': 'NRML',
                'variety': 'regular',
                'order_type': 'LIMIT',
                'quantity': int(option.lot_size) if option.lot_size.is_integer() else option.lot_size,
                'price': option.last_price
            })

        for chunk in Utilities.divide_chunks(input_list=data, chunk_size=chunk_size):
            response = requests.post(
                'https://kite.zerodha.com/oms/margins/orders',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
                },
                data=json.dumps(chunk)
            )

            if response.status_code != 200:
                raise Exception('Invalid response code found: %s, expected: 200, response: %s' % (response.status_code, response.text))

            return_data += response.json()['data']

        return [from_dict(data_class=OptionMarginModel, data=option_margin) for option_margin in return_data]
