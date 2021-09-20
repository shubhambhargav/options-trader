import requests
from dacite import from_dict

from src.apps.settings.controllers import ConfigController

from ..models import ScreenModel


class ScreensController:
    @staticmethod
    def load_screen(screen_id: str) -> ScreenModel:
        config = ConfigController.get_config()

        response = requests.get(
            'https://api.tickertape.in/screener/screens/load/%s' % screen_id,
            headers={
                'Cookie': f'jwt={config.tickertape_jwt_token};',
                'x-csrf-token': config.tickertape_csrf_token
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        screen_data = response.json()['data']

        return from_dict(data_class=ScreenModel, data=screen_data)
