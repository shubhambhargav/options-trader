import json
from dataclasses import asdict
from src.apps.kite.models import positions
from typing import List

import requests
from dacite import from_dict

from ..models import GTTModel

import src.utilities as Utilities
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

        if response.status_code != 200:
            raise Exception('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))

    @staticmethod
    def delete_gtt(gtt: GTTModel):
        response = requests.delete(
            'https://kite.zerodha.com/oms/gtt/triggers/%s' % gtt.id,
            headers={
                'Authorization': f'enctoken {KITE_AUTH_TOKEN}'
            }
        )

        if response.status_code != 200:
            raise Exception('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))

    @staticmethod
    def remove_naked_gtts(positions: List[positions.PositionModel]):
        gtts = GTTController.get_gtts()

        position_map = dict((position.tradingsymbol, position) for position in positions)

        for gtt in gtts:
            metadata = Utilities.tradingsymbol_to_meta(tradingsymbol=gtt.condition.tradingsymbol)

            # Currently only implemented for FUTURES coverage
            if metadata['type'] != 'FUT':
                continue

            tradingsymbol = '%(instrument)s%(datetime)s%(price)sPE' % {
                'instrument': metadata['instrument'],
                'datetime': metadata['datetime'],
                'price': gtt.condition.trigger_values[0]
            }

            if position_map.get(tradingsymbol):
                LOGGER.debug('Found corresponding position for the GTT, skipping removal...')

                continue

            GTTController.delete_gtt(gtt=gtt)

            LOGGER.info('Removed GTT for %s, price: %s because no corresponding position was found...' % (
                gtt.condition.tradingsymbol, gtt.condition.trigger_values[0]
            ))
