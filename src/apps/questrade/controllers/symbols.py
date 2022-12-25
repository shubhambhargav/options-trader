import requests

from datetime import date
from typing import List

from dacite import from_dict
from src.apps.settings.controllers import ConfigController

from ..models import CandleModel


class SymbolsController:
    @staticmethod
    def get_symbol_candles(symbol_id: str, start: date, end: date, interval: str = 'OneDay') -> List[CandleModel]:
        response = requests.get(
            'https://api06.iq.questrade.com/v1/markets/candles/%(symbol_id)s?startTime=%(start)s&endTime=%(end)s&interval=%(interval)s' % {
                'symbol_id': symbol_id,
                'start': start.strftime('%Y-%m-%dT00:00:00-05:00'),
                'end': end.strftime('%Y-%m-%dT00:00:00-05:00'),
                'interval': interval
            },
            headers={
                'Authorization': f'Bearer {ConfigController.get_config().questrade_access_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        candles: List[CandleModel] = []

        for row in response.json()['candles']:
            candles.append(from_dict(data_class=CandleModel, data=row))

        return candles
