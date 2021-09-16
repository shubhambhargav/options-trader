from typing import List

import requests
from datetime import timedelta
from dacite import from_dict

from .gtt import GTTController

from ..models import PositionModel
from .._variables import VARIABLES
from .. import utilities as Utilities


class NakedPositionCover:
    @staticmethod
    def cover_option_sell(position: PositionModel, future_symbol: str, option_meta: dict):
        if not isinstance(position, PositionModel):
            position = from_dict(data_class=PositionModel, data=position)

        expiry = Utilities.get_last_thursday_for_derivative(datetime_str=option_meta['datetime'])

        gtt = {
            'condition': {
                'exchange': 'NFO',
                'tradingsymbol': future_symbol,
                'trigger_values': [option_meta['option_price']],
                # Note: Following is a field check in Zerodha, isn't really required
                # but the API responds with InputException if this field is not provided
                # Any other value less than option_price also does not work due to checks
                'last_price': option_meta['option_price'] + 100
            },
            'orders': [{
                'exchange': 'NFO',
                'tradingsymbol': future_symbol,
                'transaction_type': 'SELL',
                # TODO: Following assumes the option to always be in the SELL mode. This needs
                #       to change for BUY mode.
                'quantity': abs(position.quantity),
                'price': option_meta['option_price'],
                'order_type': 'LIMIT',
                'product': 'NRML'
            }],
            'type': 'single',
            'expires_at': (expiry + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        }

        GTTController.place_gtt(gtt=gtt)


class PositionsController:
    @staticmethod
    def get_positions() -> List[PositionModel]:
        response = requests.get(
            'https://kite.zerodha.com/oms/portfolio/positions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
            }
        )

        if response.status_code not in [200, 304]:
            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        return [PositionModel(**position) for position in response.json()['data']['net']]

    @staticmethod
    def cover_naked_positions():
        """
        TODO: Cover positions other than long options
        """
        positions = PositionsController.get_positions()
        gtts = GTTController.get_gtts()

        uncovered_option_positions = []
        gtt_tradingsymbol = set([elem.condition.tradingsymbol for elem in gtts])

        for position in sorted(positions, key=lambda x: x.tradingsymbol):
            if position.tradingsymbol.endswith('PE'):
                uncovered_option_positions.append(position)

            if position.tradingsymbol.endswith('FUT'):
                uncovered_option_positions.pop(-1)

        for option_position in uncovered_option_positions:
            option_meta = Utilities.tradingsymbol_to_meta(tradingsymbol=option_position.tradingsymbol)

            # TODO: Find a better way to find the respective future for an option cover
            tradingsymbol = '%(instrument)s%(datetime)sFUT' % {
                'instrument': option_meta['instrument'],
                'datetime': option_meta['datetime']
            }

            if tradingsymbol in gtt_tradingsymbol:
                print('Found existing future for: %s, skipping...' % tradingsymbol)

                continue

            NakedPositionCover.cover_option_sell(
                position=option_position,
                future_symbol=tradingsymbol,
                option_meta=option_meta
            )
