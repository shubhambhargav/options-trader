from typing import List
import json

import requests
from dacite import from_dict

from ..models import OptionFilterModel, OptionQuoteModel, OptionModel

from src.apps.settings.controllers import ConfigController


class OptionsController:
    @staticmethod
    def get_option_quotes(ids: List[int], option_filters: List[OptionFilterModel] = []) -> List[OptionQuoteModel]:
        response = requests.post(
            'https://api01.iq.questrade.com/v1/markets/quotes/options',
            data=json.dumps({
                'filters': [option_filter.to_json() for option_filter in option_filters],
                'optionIds': ids
            }),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {ConfigController.get_config().questrade_access_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        option_quotes: List[OptionQuoteModel] = []

        for row in response.json()['optionQuotes']:
            option_quotes.append(from_dict(data_class=OptionQuoteModel, data=row))

        return option_quotes

    @staticmethod
    def get_options(symbol_id: int) -> List[OptionModel]:
        response = requests.get(
            'https://api01.iq.questrade.com/v1/symbols/%s/options' % symbol_id,
            headers={
                'Authorization': f'Bearer {ConfigController.get_config().questrade_access_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        options: List[OptionModel] = []

        for row in response.json()['optionChain']:
            options.append(from_dict(data_class=OptionModel, data=row))

        return options
