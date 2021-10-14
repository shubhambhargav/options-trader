from typing import List

import requests
from dacite import from_dict

from src.apps.tickertape.models import SearchResponseItem, StockSidModel


class SearchController:
    @staticmethod
    def search(text: str, types: list = ['stock', 'index', 'etf', 'mutualfund']) -> List[SearchResponseItem]:
        response = requests.get(
            'https://api.tickertape.in/search?text=%(text)s&types=%(types)s' % {
                'text': text,
                'types': ','.join(types)
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        response_data = response.json()['data']

        search_items = response_data['stocks'] + response_data['indices']

        return [from_dict(data_class=SearchResponseItem, data=search_item) for search_item in search_items]

    @staticmethod
    def find_stocks(sids: list = []) -> List[StockSidModel]:
        response = requests.get(
            'https://api.tickertape.in/watchlists/data?sids=%(sids)s' % {
                'sids': ','.join(sids)
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        stocks = response.json()['data']

        return [from_dict(data_class=StockSidModel, data=stock) for stock in stocks]
