from src.apps.kite.controllers.gtt import KITE_AUTH_TOKEN
import requests
from typing import List, Optional

from dacite import from_dict

from src.apps.settings.controllers import ConfigController

from ..models import HoldingModel

KITE_AUTH_TOKEN = ConfigController.get_config().kite_auth_token


class HoldingsController:
    @staticmethod
    def get_holdings() -> List[HoldingModel]:
        response = requests.get(
            'https://kite.zerodha.com/oms/portfolio/holdings',
            headers={
                'Authorization': f'enctoken {KITE_AUTH_TOKEN}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        holdings = response.json()['data']

        return [from_dict(data_class=HoldingModel, data=holding) for holding in holdings]

    @staticmethod
    def get_holding(tradingsymbol: str) -> Optional[HoldingModel]:
        holdings = HoldingsController.get_holdings()

        for holding in holdings:
            if holding.tradingsymbol == tradingsymbol:
                return holding

        return None
