import requests
from typing import List

from dacite import from_dict

from src._variables import VARIABLES

from ..models import HoldingModel


@staticmethod
class HoldingsController:
    @staticmethod
    def get_holdings() -> List[HoldingModel]:
        response = requests.get(
            'https://kite.zerodha.com/oms/portfolio/holdings',
            headers={
                'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        holdings = response.json()['data']

        return [from_dict(data_class=HoldingModel, data=holding) for holding in holdings]
