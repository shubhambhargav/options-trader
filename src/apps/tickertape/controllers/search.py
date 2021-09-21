from typing import List

import requests
from dacite import from_dict

from src.apps.tickertape.models import SearchResponseItem


class SearchController:
    @staticmethod
    def search(text: str, types: list = ['stock', 'brands', 'index', 'etf', 'mutualfund']) -> List[SearchResponseItem]:
        response = requests.get(
            'https://api.tickertape.in/search?text=%(text)s&types=%(types)s' % {
                'text': text,
                'types': ','.join(types)
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        response_data = response.json()['data']

        search_items = response_data['stocks'] + response_data['brands'] + response_data['indices']

        return [from_dict(data_class=SearchResponseItem, data=search_item) for search_item in search_items]

