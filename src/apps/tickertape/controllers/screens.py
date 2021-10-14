from typing import List
import requests
from dacite import from_dict

from src.apps.settings.controllers import ConfigController

from ..models import ScreenModel, ScreenListModel

CONFIG = ConfigController.get_config()
JWT_TOKEN = CONFIG.tickertape_jwt_token
CSRF_TOKEN = CONFIG.tickertape_csrf_token


class ScreensController:
    @staticmethod
    def list_screens() -> List[ScreenListModel]:
        response = requests.get(
            'https://api.tickertape.in/screener/screens',
            headers={
                'Cookie': f'jwt={JWT_TOKEN};',
                'x-csrf-token': CSRF_TOKEN
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        screens = response.json()['data']

        return [from_dict(data_class=ScreenListModel, data=screen) for screen in screens]

    @staticmethod
    def load_screen(screen_id: str) -> ScreenModel:
        response = requests.get(
            'https://api.tickertape.in/screener/screens/load/%s' % screen_id,
            headers={
                'Cookie': f'jwt={JWT_TOKEN};',
                'x-csrf-token': CSRF_TOKEN
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        screen_data = response.json()['data']

        return from_dict(data_class=ScreenModel, data=screen_data)
