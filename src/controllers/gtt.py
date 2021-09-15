import json
from dataclasses import asdict
from typing import List

import requests
from dacite import from_dict

from ..models import GTTModel
from .._variables import VARIABLES


class GTTController:
    @staticmethod
    def get_gtts() -> List[GTTModel]:
        headers = {
            'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
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
            'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
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
            print('Successfully placed the order for %s' % gtt.condition.tradingsymbol)

            return

        raise Exception('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))

