from typing import List

import requests
from dacite import from_dict

from src.apps.settings.controllers import ConfigController

from ..models import CustomUniverseModel


class CustomUniversesController:
    @staticmethod
    def get_custom_universes() -> List[CustomUniverseModel]:
        config = ConfigController.get_config()

        response = requests.get(
            'https://api.tickertape.in/screener/customUniverses',
            headers={
                'Cookie': f'jwt={config.tickertape_jwt_token};',
                'x-csrf-token': config.tickertape_csrf_token
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        custom_universes = response.json()['data']['customUniverses']

        return [from_dict(data_class=CustomUniverseModel, data=custom_universe) for custom_universe in custom_universes]
