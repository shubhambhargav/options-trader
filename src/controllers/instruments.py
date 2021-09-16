import json
from typing import List
import requests
from dacite import from_dict

from ..models import InstrumentModel, OptionModel


class InstrumentsController:
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
    def get_options_chain(instrument: InstrumentModel) -> List[OptionModel]:
        response = requests.get(
            'https://api.sensibull.com/v1/instruments/%s' % instrument.tickersymbol
        )

        if response.status_code != 200:
            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        return [from_dict(data_class=OptionModel, data=option) for option in response.json()['data']]
