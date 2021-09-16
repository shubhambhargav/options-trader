from dataclasses import asdict
import emoji
import pandas as pd

from ._variables import VARIABLES
from .controllers import PositionsController


def get_positions_df():
    positions = PositionsController.get_positions()

    return pd.DataFrame([asdict(position) for position in positions])


def add_positions(options_df):
    positions_df = get_positions_df()
    positions_df = positions_df.rename(columns={'quantity': 'existing'})
    purchased_instrument_df = pd.DataFrame(positions_df['tradingsymbol'] \
        .str.extract('([A-Z]+)', expand=False)) \
        .rename(columns={'tradingsymbol': 'base_underlying_instrument'})
    purchased_instrument_df['underlying_instrument'] = purchased_instrument_df['base_underlying_instrument'] \
        .apply(
            lambda x: emoji.emojize(x + ' :white_check_mark:', use_aliases=True)
        )

    options_df = options_df \
        .set_index('tradingsymbol') \
        .join(positions_df[['existing', 'tradingsymbol']].set_index('tradingsymbol'))

    options_df['existing'] = options_df['existing'] / options_df['lot_size']
    options_df['existing'] = options_df['existing'] \
        .apply(
            lambda x: emoji.emojize(str(int(-1 * x)) + ' :white_check_mark:', use_aliases=True) if x <= -1 else 'NA'
        )
    options_df \
        .rename(columns={'underlying_instrument': 'old_underlying_instrument'}, inplace=True)

    options_df = options_df \
        .join(
            purchased_instrument_df.set_index(['base_underlying_instrument']),
            how='left',
            on='old_underlying_instrument'
        )
    options_df['underlying_instrument'].fillna(options_df['old_underlying_instrument'], inplace=True)

    return options_df
