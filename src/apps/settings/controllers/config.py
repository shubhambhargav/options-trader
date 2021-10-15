import json
import requests
from dacite import from_dict

from src.external.chrome import get_cookie_dict

from src.apps.settings.models import ConfigModel
from src.external.pyotp.totp import TOTP

KITE_CONFIG_FILE = './config.json'


class ConfigController:
    CONFIG: ConfigModel = None

    @staticmethod
    def get_kite_enctoken():
        config = json.loads(open(KITE_CONFIG_FILE, 'r').read())

        if not config.get('user_id'):
            raise ValueError('user_id not found in config')

        if not config.get('password'):
            raise ValueError('password not found in config')

        if not config.get('totp_key'):
            raise ValueError('totp_key not found in config')

        session = requests.Session()

        response = session.post(
            'https://kite.zerodha.com/api/login',
            data={
                'user_id': config['user_id'],
                'password': config['password']
            }
        )

        if response.status_code != 200:
            session.close()

            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        request_id = response.json()['data']['request_id']

        response = session.post(
            'https://kite.zerodha.com/api/twofa',
            data={
                'user_id': config['user_id'],
                'request_id': request_id,
                'twofa_value': TOTP(config['totp_key']).now(),
                'skip_session': ''
            }
        )

        if response.status_code != 200:
            session.close()

            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        session.close()

        return response.cookies.get('enctoken')

    @staticmethod
    def is_kite_token_invalid(enctoken: str):
        response = requests.get(
            'https://kite.zerodha.com/oms/portfolio/holdings',
            headers={
                'Authorization': f'enctoken {enctoken}'
            }
        )

        return True if response.status_code != 200 else False

    @staticmethod
    def refresh_kite_enctoken():
        kite_enctoken = get_cookie_dict(domain_name='kite.zerodha.com').get('enctoken')

        if ConfigController.is_kite_token_invalid(enctoken=kite_enctoken):
            kite_enctoken = ConfigController.get_kite_enctoken()

        ConfigController.CONFIG.kite_auth_token = kite_enctoken

    @staticmethod
    def get_config() -> ConfigModel:
        if ConfigController.CONFIG:
            return ConfigController.CONFIG

        config = {}

        # TODO: Add mechanism to refresh the token
        kite_cookie_dict = get_cookie_dict(domain_name='kite.zerodha.com')
        tickertape_cookie_dict = get_cookie_dict(domain_name='tickertape.in')

        kite_enctoken = kite_cookie_dict.get('enctoken')

        if ConfigController.is_kite_token_invalid(enctoken=kite_enctoken):
            kite_enctoken = ConfigController.get_kite_enctoken()

        config.update({
            'kite_auth_token': kite_enctoken,
            'tickertape_csrf_token': tickertape_cookie_dict['x-csrf-token-tickertape'],
            'tickertape_jwt_token': tickertape_cookie_dict['jwt']
        })

        ConfigController.CONFIG = from_dict(data_class=ConfigModel, data=config)

        return ConfigController.CONFIG
