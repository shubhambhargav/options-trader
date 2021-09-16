import json
from typing import List
from datetime import datetime, timedelta

import requests
from dacite import from_dict

from .._variables import VARIABLES
from ..models import InstrumentModel, CandleModel, OptionModel
from .. import utilities as Utilities


class InstrumentsController:
    INSTRUMENT_TOKEN_DICT = None

    @staticmethod
    def get_instrument_token_dict() -> dict:
        # Since instrument token don't change often, we are caching them for subsequent calls
        if InstrumentsController.INSTRUMENT_TOKEN_DICT:
            return InstrumentsController.INSTRUMENT_TOKEN_DICT

        response = requests.get('https://api.kite.trade/instruments')

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        instruments = Utilities.csv_text_to_dict(response.text)
        instrument_token_dict = {}

        for instrument in instruments:
            instrument_token_dict[instrument['tradingsymbol']] = instrument['instrument_token']

        InstrumentsController.INSTRUMENT_TOKEN_DICT = instrument_token_dict

        return instrument_token_dict

    @staticmethod
    def get_instrument(tickersymbol: str) -> InstrumentModel:
        """Legacy function from options module"""
        # TODO: Possibly retire this function
        response = requests.post(
            'https://api.sensibull.com/v1/instrument_details',
            headers={
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'underlyings': [tickersymbol]
            })
        )

        if response.status_code != 200:
            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        data = response.json()

        if not data.get(tickersymbol):
            raise Exception('No options getting traded for %s' % tickersymbol)

        # Response contains instrument ID as a key, hence to maintain the sanity of the function
        # the response enusures that we are only sending the respective instrument details
        instrument = json.loads(list(data.values())[0])

        # Following is being done to account for @dataclass compatibility
        # with class attributes only starting with non-digit characters
        instrument.pop('200DMA_volume', None)

        instrument['tickersymbol'] = tickersymbol

        return from_dict(data_class=InstrumentModel, data=instrument)

    @staticmethod
    def get_instrument_candles(tickersymbol: str) -> List[CandleModel]:
        insturment_token_dict = InstrumentsController.get_instrument_token_dict()
        config = VARIABLES.CONFIG

        # Following is documented here: https://kite.trade/docs/connect/v3/historical/
        response_headers = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        tickersymbol_backup = {
            'BANKNIFTY': 'NIFTY BANK',
            'NIFTY': '256265'
        }

        instrument_token = insturment_token_dict[tickersymbol] if tickersymbol in insturment_token_dict else tickersymbol_backup[tickersymbol]

        response = requests.get(
            'https://kite.zerodha.com/oms/instruments/historical/%(instrument_token)s/day?user_id=%(user_id)s&oi=1&from=%(from)s&to=%(to)s' % {
                'instrument_token': instrument_token,
                'user_id': config['user_id'],
                'from': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            },
            headers={
                'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        instrument_candles = []

        for row in response.json()['data']['candles']:
            instrument_candles.append(from_dict(data_class=CandleModel, data=dict(zip(response_headers, row))))

        return instrument_candles

    @staticmethod
    def get_options_chain(instrument: InstrumentModel) -> List[OptionModel]:
        response = requests.get(
            'https://api.sensibull.com/v1/instruments/%s' % instrument.tickersymbol
        )

        if response.status_code != 200:
            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        return [from_dict(data_class=OptionModel, data=option) for option in response.json()['data']]
