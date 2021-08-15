import requests
import emoji
import pandas as pd

from ._variables import VARIABLES


def get_positions():
    response = requests.get(
        'https://kite.zerodha.com/oms/portfolio/positions',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
        }
    )

    if response.status_code not in [200, 304]:
        raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

    return response.json()['data']


def get_positions_df():
    positions_response = get_positions()

    positions = positions_response['net'] + positions_response['day']

    return pd.DataFrame(positions)


def add_positions(options_df):
    positions_df = get_positions_df()
    positions_df = positions_df.rename(columns={'quantity': 'existing'})
    options_df = options_df \
        .set_index('tradingsymbol') \
        .join(positions_df[['existing', 'tradingsymbol']].set_index('tradingsymbol'))

    options_df['existing'] = options_df['existing'] / options_df['lot_size']
    options_df['existing'] = options_df['existing'] \
        .apply(
            lambda x: emoji.emojize(str(int(-1 * x)) + ' :white_check_mark:', use_aliases=True) if x <= -1 else 'NA'
        )

    return options_df
