from dataclasses import dataclass

from src.apps.tickertape.models import ScreenListModel, CustomUniverseModel


@dataclass
class ConfigModel:
    tickertape_screen: ScreenListModel
    purchased_stocks_universe: CustomUniverseModel
