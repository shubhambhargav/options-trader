import requests

from datetime import date
from typing import List

from dacite import from_dict
from src.apps.settings.controllers import ConfigController

from ..models import CandleModel, SymbolModel


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

    @staticmethod
    def get_symbols(ids: list = [], names: list = []) -> List[SymbolModel]:
        if not ids and not names:
            raise ValueError('Either ids or names must be provided')

        values = ids if ids else names

        response = requests.get(
            'https://api06.iq.questrade.com/v1/symbols?%(param)s=%(value)s' % {
                'param': 'ids' if ids else 'names',
                'value': ','.join([str(val) for val in values])
            },
            headers={
                'Authorization': f'Bearer {ConfigController.get_config().questrade_access_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        symbols: List[CandleModel] = []

        for row in response.json()['symbols']:
            symbols.append(from_dict(data_class=SymbolModel, data=row))

        return symbols

    @staticmethod
    def get_symbol(id: int = None, name: str = None) -> SymbolModel:
        if not id and not name:
            raise ValueError('Either id or name must be provided')

        url = 'https://api06.iq.questrade.com/v1/symbols/%s' % id if id else 'https://api06.iq.questrade.com/v1/symbols?names=%s' % name

        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {ConfigController.get_config().questrade_access_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        return from_dict(data_class=SymbolModel, data=response.json()['symbols'][0])
