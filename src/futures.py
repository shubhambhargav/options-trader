import json
import requests
from datetime import datetime

from ._variables import VARIABLES
from . import utilities as Utilities


def place_gtt_for_option(option: dict):
    tradingsymbol = '%(instrument)s%(datetime)sFUT' % {
        'instrument': option['instrument'],
        'datetime': option['datetime']
    }

    data = {
        'condition': json.dumps({
            'exchange': 'NFO',
            'tradingsymbol': tradingsymbol,
            'trigger_values': [option['option_price']],
            # Note: Following is a field check in Zerodha, isn't really required
            # but the API responds with InputException if this field is not provided
            # Any other value less than option_price also does not work due to checks
            'last_price': option['option_price'] + 100
        }),
        'orders': json.dumps([{
            'exchange': 'NFO',
            'tradingsymbol': tradingsymbol,
            'transaction_type': 'SELL',
            # TODO: Following assumes the option to always be in the SELL mode. This needs
            #       to change for BUY mode.
            'quantity': int(-1 * option['overnight_quantity']),
            'price': option['option_price'],
            'order_type': 'LIMIT',
            'product': 'NRML'
        }]),
        'type': 'single',
        # TODO: Update the following to be the date when the option expires
        'expires_at': '2022-08-25 00:00:00'
    }

    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
    }

    response = requests.post(
        'https://kite.zerodha.com/oms/gtt/triggers',
        headers=headers,
        data=data
    )

    if response.status_code == 200:
        print('Successfully placed the order for %s' % tradingsymbol)

        return

    print('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))
