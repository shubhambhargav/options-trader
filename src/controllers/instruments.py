import requests

from ..models import Instrument as InstrumentModel


class InstumentsController:
    def __init__(self):
        pass

    def get_options_chain(self, instrument: InstrumentModel):
        response = requests.get(
            'https://api.sensibull.com/v1/instruments/%s' % instrument.instrument_token
        )

        if response.status_code != 200:
            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        return response.json()['data']
