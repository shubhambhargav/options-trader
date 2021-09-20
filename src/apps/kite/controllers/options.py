from collections import defaultdict
from dataclasses import asdict
import json
from src.apps.kite.models.base import StockOfInterest
from src.apps.kite.controllers.positions import PositionsController
from typing import List
from dacite import from_dict

import requests

from .instruments import InstrumentsController
from .users import UsersController

from ..models import (
    OptionModel,
    OptionMarginModel,
    EnrichedOptionModel
)
import src.utilities as Utilities
from src._variables import VARIABLES
from src.logger import LOGGER


class OptionsController:
    @staticmethod
    def get_option_last_price(option: EnrichedOptionModel) -> float:
        if not isinstance(option, EnrichedOptionModel):
            option = from_dict(data_class=EnrichedOptionModel, data=option)

        # TODO: Find a better way to get the last price. Currently we are getting
        #       the entire option chain to get the last price of an option
        option_chain = InstrumentsController.get_options_chain(instrument=option.instrument_data)

        for option_elem in option_chain:
            if option_elem.tradingsymbol == option.tradingsymbol:
                return option.last_price

        return None

    @staticmethod
    def sell_option(option: EnrichedOptionModel):
        # Since the price of the option can change during the analysis,
        # following code ensures that we don't trade at a lower value than the last price
        if not isinstance(option, EnrichedOptionModel):
            option = from_dict(data_class=EnrichedOptionModel, data=option)

        option_last_price = OptionsController.get_option_last_price(option=option)
        expected_trade_price = option.last_price

        if option_last_price > expected_trade_price:
            LOGGER.debug(
                'Increasing the trade price for %s. Previous price: %s, new price: %s' % (
                    option.name, expected_trade_price, option_last_price
                )
            )
            LOGGER.debug('New expected profit: %s' % (expected_trade_price * int(option.lot_size)))

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
            'user_id': UsersController.get_current_user().user_id,
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
            LOGGER.info('Successfully placed the order for %s' % option.name)

            return

        LOGGER.error('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))

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

    @staticmethod
    def enrich_options(options: List[OptionModel]) -> List[EnrichedOptionModel]:
        enriched_options = []
        margin_data = OptionsController.get_option_margin_bulk(options=options)
        positions = PositionsController.get_positions()

        instrument_positions = defaultdict(list)
        option_positions = defaultdict()

        for position in positions:
            instrument_positions[position.underlying_instrument].append(position)
            option_positions[position.tradingsymbol] = position

        # Following is used to avoid multiple calls to the underlying instrument API
        instruments = list(set([option.underlying_instrument for option in options]))
        instruments_data = dict((instrument, InstrumentsController.get_instrument(tickersymbol=instrument)) for instrument in instruments)

        enriched_instruments_data = InstrumentsController.enrich_instruments(
            instruments=[from_dict(data_class=StockOfInterest, data={'tickersymbol': instrument}) for instrument in instruments]
        )
        enriched_instruments_data = dict((instrument.tickersymbol, instrument) for instrument in enriched_instruments_data)

        for iteration, option in enumerate(options):
            option = EnrichedOptionModel(**asdict(option))

            option.position = option_positions.get(option.tradingsymbol)
            option.instrument_positions = instrument_positions.get(option.underlying_instrument)
            option.margin = margin_data[iteration]
            option.profit_percentage = (option.profit / option.margin.total) * 100

            enriched_options.append(option)

        for option in enriched_options:
            option.instrument_data = instruments_data[option.underlying_instrument]
            option.percentage_dip = (option.instrument_data.last_price - option.strike) / option.instrument_data.last_price * 100
            option.enriched_instrument = enriched_instruments_data[option.underlying_instrument]

        return enriched_options
