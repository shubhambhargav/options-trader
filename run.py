import json
import emoji
from argparse import ArgumentParser
from os.path import isfile

from numpy import isnan

from src.apps.kite.models import *
from src.apps.kite.controllers import *
import runtime_variables as VARIABLES
from src import _variables as LibVariables
from src.options import get_options_of_interest_df, select_options
from src.external.chrome import get_cookie_dict
from src.technical_indicators import add_recommendations


def _refresh_config():
    config_loc = './config.json'

    config = json.loads(open(config_loc).read()) if isfile(config_loc) else {}

    cookie_dict = get_cookie_dict(domain_name='kite.zerodha.com')

    config['auth_token'] = cookie_dict['enctoken']

    with open(config_loc, 'w+') as fileop:
        fileop.write(json.dumps(config, indent=4))

    # Following reload is required to ensure that the new auth token is reloaded
    # to the underlying library as well
    LibVariables.reload()


def _get_args():
    parser = ArgumentParser(description='Get options of interest...')
    parser.add_argument(
        '--custom-filtered', dest='custom_filter_enabled', action='store_true',
        default=False, help='Only use custom filtered stocks...'
    )
    parser.add_argument(
        '--no-order', dest='is_order_enabled', action='store_false',
        default=True, help='Enabling ordering or not'
    )
    parser.add_argument(
        '--stocks', dest='stocks', type=str,
        help='List of stocks to process, defaults minimum drop to 3'
    )

    args = parser.parse_args()

    if args.stocks:
        args.stocks = [
            {'tickersymbol': stock_name, 'custom_filters': { 'minimum_dip': 3 }} \
                for stock_name in args.stocks.split(',')
        ]

    return args


def run():
    _refresh_config()

    args = _get_args()

    print('Total profit expected till now: %d' % PositionsController.get_pnl_month_end())

    if args.is_order_enabled:
        PositionsController.cover_naked_positions()

    stocks = VARIABLES.OPTIONS_OF_INTEREST if not args.stocks else args.stocks

    if args.custom_filter_enabled:
        stocks = [stock for stock in stocks if stock.get('custom_filters')]

    options_df = get_options_of_interest_df(stocks=stocks)

    if len(options_df) == 0:
        print('No eligible options found...')

        return

    options_df.sequence_id = options_df.sequence_id.fillna(-100).astype(int)
    order_options_df = options_df.copy(deep=True)

    # Add metadata about current positions
    options_df.underlying_instrument[options_df.instrument_positions.notnull()] = options_df.underlying_instrument.apply(
        lambda x: emoji.emojize(x + ' :white_check_mark:', use_aliases=True)
    )
    options_df['existing'] = 'NA'

    if 'position__quantity' in list(options_df.columns):
        options_df['existing'] = (options_df.position__quantity / options_df.lot_size).apply(
            lambda x: 'NA' if isnan(x) else emoji.emojize(str(abs(x)) + ' :white_check_mark:', use_aliases=True)
        )

    options_df.rename(
        columns={
            'sequence_id': 'seq',
            'underlying_instrument': 'instrument',
            'instrument_data__close_price': 'instrument_price',
            'percentage_dip': '%_dip',
            'profit_percentage': '%_profit',
            'margin__total': 'margin',
            'enriched_instrument__close_last_by_min': 'close_last_by_min',
            'enriched_instrument__close_last_by_avg': 'close_last_by_avg',
            'enriched_instrument__last_buy_signal': 'last_buy_signal'
        },
        inplace=True
    )

    options_df = add_recommendations(option_df=options_df)

    indexed_options = options_df \
        .sort_values(['instrument', 'expiry']) \
        .set_index(['instrument', 'instrument_price', 'expiry', 'close_last_by_min', 'close_last_by_avg', 'last_buy_signal'])

    columns = [
        'seq', 'recommendation', 'existing', '%_dip', 'profit', '%_profit', 'strike', 'last_price', 'margin', 'backup_money'
    ]

    print(indexed_options[columns].to_string())

    if args.is_order_enabled:
        selection = input('Select the options to trade: ')
        selected_options = select_options(
            options=[Utilities.unflatten_dict(data=option) for option in order_options_df.T.to_dict().values()],
            selection=selection
        )

        for option in selected_options:
            OptionsController.sell_option(option=option)


if __name__ == '__main__':
    run()
