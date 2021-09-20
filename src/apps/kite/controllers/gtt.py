import json
from dataclasses import asdict
from src.apps.kite.models import positions
from typing import List

import requests
from dacite import from_dict

from ..models import GTTModel
from src.apps.settings.controllers import ConfigController
from src.logger import LOGGER

KITE_AUTH_TOKEN = ConfigController.get_config().kite_auth_token


class GTTController:
    @staticmethod
    def get_gtts() -> List[GTTModel]:
        headers = {
            'Authorization': f'enctoken {KITE_AUTH_TOKEN}'
        }

        response = requests.get(
            'https://kite.zerodha.com/oms/gtt/triggers',
            headers=headers
        )

        if response.status_code != 200:
            raise ValueError('Failed to get existing GTT from Kite')

        return [from_dict(data_class=GTTModel, data=gtt) for gtt in response.json()['data']]

    @staticmethod
    def place_gtt(gtt: GTTModel):
        if not isinstance(gtt, GTTModel):
            gtt = from_dict(data_class=GTTModel, data=gtt)

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'Authorization': f'enctoken {KITE_AUTH_TOKEN}'
        }

        gtt_payload = asdict(gtt)

        # Following is being done to conform to the expected payload structure in Zerodha APIs
        gtt_payload['orders'] = json.dumps(gtt_payload['orders'])
        gtt_payload['condition'] = json.dumps(gtt_payload['condition'])

        response = requests.post(
            'https://kite.zerodha.com/oms/gtt/triggers',
            headers=headers,
            data=gtt_payload
        )

        if response.status_code == 200:
            LOGGER.info('Successfully placed the order for %s' % gtt.condition.tradingsymbol)

            return

        raise Exception('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))

    @staticmethod
    def cover_naked_gtts(positions: List[positions.PositionModel]):
        raise Exception('This functionality has not been implemented yet...')

        gtts = GTTController.get_gtts()

        position_map = {}

        # TODO: Implement this
