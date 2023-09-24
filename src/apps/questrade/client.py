from questrade_api import Questrade

from src.apps.settings.controllers import ConfigController


class QuestradeClient:
    _self = None
    Q = None

    def __init__(self):
        pass

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)

        return cls._self

    def initialize(self):
        if not self.Q:
            self.Q = Questrade(refresh_token=ConfigController.get_config().questrade_refresh_token)

        return self.Q

    def destroy(self):
        config = ConfigController.get_config()

        config.questrade_refresh_token = self.Q.auth.token['refresh_token']

        ConfigController.update_config(config=config)

        self.Q = None
