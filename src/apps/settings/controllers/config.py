from dacite import from_dict

from src.external.chrome import get_cookie_dict

from ..models import ConfigModel


class ConfigController:
    CONFIG = None

    @staticmethod
    def get_config() -> ConfigModel:
        if ConfigController.CONFIG:
            return ConfigController.CONFIG

        config = {}

        kite_cookie_dict = get_cookie_dict(domain_name='kite.zerodha.com')
        tickertape_cookie_dict = get_cookie_dict(domain_name='tickertape.in')

        config.update({
            'kite_auth_token': kite_cookie_dict['enctoken'],
            'tickertape_csrf_token': tickertape_cookie_dict['x-csrf-token-tickertape'],
            'tickertape_jwt_token': tickertape_cookie_dict['jwt']
        })

        ConfigController.CONFIG = from_dict(data_class=ConfigModel, data=config)

        return ConfigController.CONFIG
