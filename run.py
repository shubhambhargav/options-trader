import json
import pandas as pd
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
import requests

import runtime_variables as VARIABLES
from src import _variables as LibVariables
from src.options import get_options_of_interest_df, select_options
from src.orders import place_order
from src.chrome import get_cookie_dict
from src.instruments import get_enriched_instruments_df
from src.technical_indicators import add_recommendations
from src.positions import add_positions, get_positions
from src.utilities import tradingsymbol_to_meta
from src.futures import place_gtt_for_option
from src.gtt import get_gtt


def _refresh_config():
    config_loc = './config.json'
    config = json.loads(open(config_loc).read())

    cookie_dict = get_cookie_dict()

    config['auth_token'] = cookie_dict['enctoken']

    with open(config_loc, 'w+') as fileop:
        fileop.write(json.dumps(config, indent=4))

    # Following reload is required to ensure that the new auth token is reloaded
    # to the underlying library as well
    LibVariables.reload()


def _get_indicators():
    return get_enriched_instruments_df(insturments_of_interest=VARIABLES.OPTIONS_OF_INTEREST)


def _get_future_option_diff(positions: list):
    diff_array = []

    for position in sorted(positions, key=lambda x: x['tradingsymbol']):
        if position['tradingsymbol'].endswith('PE'):
            diff_array.append(position)

        if position['tradingsymbol'].endswith('FUT'):
            diff_array.pop(-1)

    for opt in diff_array:
        opt.update(tradingsymbol_to_meta(tradingsymbol=opt['tradingsymbol']))

    return diff_array


def _set_future_gtts():
    positions = get_positions()
    gtts = get_gtt()

    gtt_tradingsymbol = set([elem['condition']['tradingsymbol'] for elem in gtts])

    uncovered_options = _get_future_option_diff(positions=positions['net'])

    for option in uncovered_options:
        # TODO: Remove / increase the stoploss for the options
        # TODO: Convert the following in a utility function
        tradingsymbol = '%(instrument)s%(datetime)sFUT' % {
            'instrument': option['instrument'],
            'datetime': option['datetime']
        }

        if tradingsymbol in gtt_tradingsymbol:
            print('Found existing future for: %s, skipping...' % tradingsymbol)

            continue

        place_gtt_for_option(option=option)


def _get_total_profit_month_end():
    positions = get_positions()
    total_profit = 0

    for position in positions['net']:
        total_profit += (-1 * position['quantity'] * position['average_price'])

    return total_profit


def run():
    _refresh_config()

    total_profit = _get_total_profit_month_end()

    print('Total profit expected till now: %d' % total_profit)

    _set_future_gtts()

    options_of_interest_df = get_options_of_interest_df(stocks=VARIABLES.OPTIONS_OF_INTEREST)

    if len(options_of_interest_df) == 0:
        print('No eligible options found...')

        return

    indicators_df = _get_indicators()
    options_of_interest_df = options_of_interest_df.join(
        indicators_df,
        how='outer',
        on='underlying_instrument'
    )
    options_of_interest_df.sequence_id = options_of_interest_df.sequence_id.fillna(-100).astype(int)
    options_of_interest_df = add_positions(options_df=options_of_interest_df)

    options_of_interest_df.rename(
        columns={
            'sequence_id': 'seq',
            'underlying_instrument': 'instrument',
            'instrument_data__close_price': 'instrument_price',
            'percentage_dip': '%_dip',
            'profit__value': 'profit',
            'profit__percentage': '%_profit',
            'margin__total': 'margin',
            ('close_last_by_min', ''): 'close_last_by_min',
            ('close_last_by_avg', ''): 'close_last_by_avg'
        },
        inplace=True
    )

    options_of_interest_df = add_recommendations(option_df=options_of_interest_df)

    indexed_options = options_of_interest_df.set_index(['instrument', 'instrument_price', 'expiry', 'close_last_by_min', 'close_last_by_avg', 'last_buy_signal'])

    columns = [
        'seq', 'recommendation', 'existing', '%_dip', 'profit', '%_profit', 'strike', 'last_price', 'margin', 'backup_money'
    ]

    print(indexed_options[columns].to_string())

    # selection = input('Select the options to trade: ')
    # selected_options = select_options(options=options_of_interest_df.T.to_dict().values(), selection=selection)

    # for option in selected_options:
    #     place_order(option=option)


if __name__ == '__main__':
    run()
