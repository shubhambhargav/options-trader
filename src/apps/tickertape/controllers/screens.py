import requests
from dacite import from_dict

from src._variables import VARIABLES

from ..models import ScreenModel


class ScreensController:
    @staticmethod
    def load_screen(screen_id: str) -> ScreenModel:
        response = requests.get(
            'https://api.tickertape.in/screener/screens/load/%s' % screen_id,
            headers={
                'Cookie': f"jwt={VARIABLES.CONFIG['tickertape_jwt_token']};",
                'x-csrf-token': VARIABLES.CONFIG['tickertape_csrf_token']
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        screen_data = response.json()['data']

        return from_dict(data_class=ScreenModel, data=screen_data)
