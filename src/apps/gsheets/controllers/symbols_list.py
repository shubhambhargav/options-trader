from typing import List
from dacite import from_dict

from src.apps.settings.controllers import ConfigController
from src.logger import LOGGER

from ..models.symbols import SymbolModel
from ..client import GoogleSheetClient

GCLIENT = GoogleSheetClient().initialize()
CONFIG = ConfigController.get_config()


class SymbolsListController:
    @staticmethod
    def get_symbols_list() -> List[SymbolModel]:
        records = GCLIENT \
            .open(CONFIG.google_sheet_name) \
            .get_worksheet_by_id(CONFIG.google_sheet_worksheet_id) \
            .get_all_records()

        # Google sheets doesn't support booleans and percentages unfortunately, hence the following translation is required
        for record in records:
            record['is_active'] = record['is_active'] == 'TRUE'

            record['percentage'] = float(record['percentage'].replace('%', '')) if record['percentage'] else None

        return [from_dict(data_class=SymbolModel, data=record) for record in records]
