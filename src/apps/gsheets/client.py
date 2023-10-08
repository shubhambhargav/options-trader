from dataclasses import asdict

import gspread

from src.apps.settings.controllers import ConfigController
from src.logger import LOGGER


class GoogleSheetClient:
    _self = None
    G = None

    def __init__(self):
        pass

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)

        return cls._self

    def initialize(self):
        if not self.G:
            config = ConfigController.get_config()

            self.G = gspread.service_account_from_dict(asdict(config.google_sheet_config))

        return self.G

