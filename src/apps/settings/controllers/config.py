import os
import json

import boto3
import requests
from dacite import from_dict

from src.external.chrome import get_cookie_dict

from src.apps.settings.models import ConfigModel
from src.external.pyotp.totp import TOTP
from settings import ENVIRONMENT, ENVIRONMENT_PRODUCTION

KITE_CONFIG_FILE = './config.json'
SECRET_MANAGER_CLIENT = boto3.client('secretsmanager')


class ConfigController:
    CONFIG: ConfigModel = None

    @staticmethod
    def get_kite_cookies(user_id: str, password: str, totp_key: str):
        cookies = {}

        session = requests.Session()

        response = session.post(
            'https://kite.zerodha.com/api/login',
            data={
                'user_id': user_id,
                'password': password
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
                'user_id': user_id,
                'request_id': request_id,
                'twofa_value': TOTP(totp_key).now(),
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
    def get_kite_enctoken(user_id: str, password: str, totp_key: str):
        return ConfigController.get_kite_cookies(user_id=user_id, password=password, totp_key=totp_key).get('enctoken')

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

        config = json.loads(open(KITE_CONFIG_FILE, 'r').read())

        if ConfigController.is_kite_token_invalid(enctoken=kite_enctoken):
            kite_enctoken = ConfigController.get_kite_enctoken(
                user_id=config['user_id'], password=config['password'], totp_key=config['totp_key']
            )

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
    def get_questrade_access_token(refresh_token: str):
        response = requests.get(
            'https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token=%(refresh_token)s' % {
                'refresh_token': refresh_token
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code from Questrade login API: %s' % response.status_code)

        return response.json()

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
    def get_remote_config() -> dict:
        remote_config = {}

        secret_key_map = {
            'kite_user_id': f'srv/options-trader/{ENVIRONMENT}/KITE_USER_ID',
            'kite_password': f'srv/options-trader/{ENVIRONMENT}/KITE_PASSWORD',
            'kite_totp_key': f'srv/options-trader/{ENVIRONMENT}/KITE_TOTP_KEY',
            'telegram_bot_token': f'srv/options-trader/{ENVIRONMENT}/TELEGRAM_BOT_TOKEN',
            'telegram_chat_id': f'srv/options-trader/{ENVIRONMENT}/TELEGRAM_CHAT_ID'
        }

        for secret_key, secret_ref in secret_key_map.items():
            remote_config[secret_key] = SECRET_MANAGER_CLIENT.get_secret_value(SecretId=secret_ref)['SecretString']

        return remote_config

    @staticmethod
    def update_config(config: ConfigModel):
        with open(KITE_CONFIG_FILE, 'w+') as fileop:
            fileop.write(json.dumps(config.__dict__, indent=4))

    @staticmethod
    def get_config() -> ConfigModel:
        if ConfigController.CONFIG:
            return ConfigController.CONFIG

        config = {}

        if ENVIRONMENT == ENVIRONMENT_PRODUCTION:
            ref_config = ConfigController.get_remote_config()

            config.update({
                'kite_auth_token': ConfigController.get_kite_enctoken(
                    user_id=ref_config['kite_user_id'], password=ref_config['kite_password'], totp_key=ref_config['kite_totp_key']
                ),
                'sensibull_access_token': 'free_user',
                'telegram_bot_token': ref_config.get('telegram_bot_token', None),
                'telegram_chat_id': ref_config.get('telegram_chat_id', None)
            })
        else:
            if os.path.exists(KITE_CONFIG_FILE):
                ref_config = json.loads(open(KITE_CONFIG_FILE, 'r').read())
            else:
                ref_config = {}

            if ref_config.get('questrade_refresh_token'):
                config.update({
                    'questrade_account_id': ref_config['questrade_account_id'],
                    'questrade_refresh_token': ref_config['questrade_refresh_token']
                })
            #     questrade_access_token = ConfigController.get_questrade_access_token(refresh_token=ref_config['questrade_refresh_token'])

            #     ref_config['questrade_refresh_token'] = questrade_access_token['refresh_token']

            #     with open(KITE_CONFIG_FILE, 'w+') as kite_config_file:
            #         kite_config_file.write(json.dumps(ref_config, indent=4))

            #     ref_config['questrade_access_token'] = questrade_access_token['access_token']

            #     config.update({
            #         'questrade_access_token': ref_config.get('questrade_access_token')
            #     })

            if ref_config.get('user_id'):
                kite_cookie_dict = get_cookie_dict(domain_name='kite.zerodha.com')
                tickertape_cookie_dict = get_cookie_dict(domain_name='tickertape.in')
                tickertape_api_cookie_dict = get_cookie_dict(domain_name='api.tickertape.in')
                sensibull_cookie_dict = get_cookie_dict(domain_name='sensibull.com')
                zerodha_cookie_dict = get_cookie_dict(domain_name='zerodha.com')
                console_cookie_dict = get_cookie_dict(domain_name='console.zerodha.com')

                kite_enctoken = kite_cookie_dict.get('enctoken')
                sensibull_access_token = sensibull_cookie_dict.get('access_token')

                if ConfigController.is_kite_token_invalid(enctoken=kite_enctoken):
                    kite_enctoken = ConfigController.get_kite_enctoken(
                        user_id=ref_config['user_id'], password=ref_config['password'], totp_key=ref_config['totp_key']
                    )

                if ConfigController.is_sensibull_access_token_valid(access_token=sensibull_access_token):
                    sensibull_access_token = ConfigController.get_sensibull_access_token()

                config.update({
                    'kite_auth_token': kite_enctoken,
                    'console_session': console_cookie_dict.get('session'),
                    'zerodha_x_csrf_token': zerodha_cookie_dict.get('public_token'),
                    'sensibull_access_token': 'free_user',
                    'tickertape_csrf_token': tickertape_cookie_dict.get('x-csrf-token-tickertape'),
                    'tickertape_jwt_token': tickertape_api_cookie_dict.get('jwt')
                })

        config.update({
            'telegram_bot_token': ref_config.get('telegram_bot_token', None),
            'telegram_chat_id': ref_config.get('telegram_chat_id', None)
        })

        ConfigController.CONFIG = from_dict(data_class=ConfigModel, data=config)

        return ConfigController.CONFIG
