import os
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
    def get_kite_cookies():
        cookies = {}

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

        cookies.update(response.cookies)

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

        cookies.update(response.cookies)

        return cookies

    @staticmethod
    def get_kite_enctoken():
        return ConfigController.get_kite_cookies().get('enctoken')

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
    def is_sensibull_access_token_valid(access_token: str):
        response = requests.get(
            'https://api.sensibull.com/v1/users/me',
            headers={
                'Authorization': f'access_token {access_token}'
            }
        )

        return True if response.status_code != 200 else False

    @staticmethod
    def refresh_sensibull_access_token():
        access_token = get_cookie_dict(domain_name='sensibull.com').get('access_token')

        if ConfigController.is_sensibull_access_token_valid(access_token=access_token):
            access_token = ConfigController.get_sensibull_access_token()

        ConfigController.CONFIG.sensibull_access_token = access_token

    @staticmethod
    def get_sensibull_access_token():
        kite_cookies = ConfigController.get_kite_cookies()

        config = json.loads(open(KITE_CONFIG_FILE, 'r').read())

        if not config.get('user_id'):
            raise ValueError('user_id not found in config')

        session = requests.Session()

        url = 'https://kite.zerodha.com/connect/login?api_key=uf8cguv719djhxfc&v=3&redirect_params=redirect_url%3Dhttps%253A//web.sensibull.com/login%253Fredirect%253D%25252F%25253Fbroker%25253Dzerodha'
        cookies = {}

        # Following is being done to accommodate for issues with the requests module in python
        # where redirect functionality doesn't forward the headers correctly
        while True:
            response = session.get(
                url,
                headers={
                    'Cookie': 'kf_session=%(kf_session)s; user_id=%(user_id)s; enctoken=%(enctoken)s' % {
                        'kf_session': kite_cookies['kf_session'],
                        'user_id': kite_cookies['user_id'],
                        'enctoken': kite_cookies['enctoken']
                    },
                },
                allow_redirects=False
            )

            cookies.update(response.cookies)

            if response.status_code == 302:
                url = response.headers.get('Location')
            else:
                break

        if response.status_code != 200:
            session.close()

            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        return cookies.get('access_token')

    @staticmethod
    def get_config() -> ConfigModel:
        if ConfigController.CONFIG:
            return ConfigController.CONFIG

        config = {}

        if os.path.exists(KITE_CONFIG_FILE):
            local_config = json.loads(open(KITE_CONFIG_FILE, 'r').read())
        else:
            local_config = {}

        kite_cookie_dict = get_cookie_dict(domain_name='kite.zerodha.com')
        tickertape_cookie_dict = get_cookie_dict(domain_name='tickertape.in')
        tickertape_api_cookie_dict = get_cookie_dict(domain_name='api.tickertape.in')
        sensibull_cookie_dict = get_cookie_dict(domain_name='sensibull.com')

        kite_enctoken = kite_cookie_dict.get('enctoken')
        sensibull_access_token = sensibull_cookie_dict.get('access_token')

        if ConfigController.is_kite_token_invalid(enctoken=kite_enctoken):
            kite_enctoken = ConfigController.get_kite_enctoken()

        if ConfigController.is_sensibull_access_token_valid(access_token=sensibull_access_token):
            sensibull_access_token = ConfigController.get_sensibull_access_token()

        config.update({
            'kite_auth_token': kite_enctoken,
            'sensibull_access_token': 'free_user',
            'tickertape_csrf_token': tickertape_cookie_dict['x-csrf-token-tickertape'],
            'tickertape_jwt_token': tickertape_api_cookie_dict['jwt'],
            'telegram_bot_token': local_config.get('telegram_bot_token', None),
            'telegram_chat_id': local_config.get('telegram_chat_id', None)
        })

        ConfigController.CONFIG = from_dict(data_class=ConfigModel, data=config)

        return ConfigController.CONFIG
