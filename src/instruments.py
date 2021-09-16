from dataclasses import asdict
from datetime import datetime, timedelta

import pandas as pd

from ._variables import VARIABLES
from . import technical_indicators
from .controllers import InstrumentsController


def _get_enriched_instrument_df(tickersymbol: str):
    instrument_candles = InstrumentsController.get_instrument_candles(tickersymbol=tickersymbol)

    instrument_df = pd.DataFrame.from_dict(data=[asdict(candle) for candle in instrument_candles])

    instrument_df['tickersymbol'] = tickersymbol

    instrument_df = technical_indicators.add_indicators(instrument_df=instrument_df)
    instrument_df = technical_indicators.add_buying_signal(instrument_df=instrument_df)

    return instrument_df


def get_enriched_instruments_df(insturments_of_interest: list):
    final_df = pd.DataFrame()

    for instrument in insturments_of_interest:
        instrument_df = _get_enriched_instrument_df(tickersymbol=instrument['ticker'])

        if final_df.empty:
            final_df = instrument_df

            continue

        final_df = pd.concat([final_df, instrument_df])

    last_buy_signal_df = final_df[(final_df['buy_signal'] == 2) & (final_df['timestamp'] >= (datetime.now() - timedelta(days=30)).strftime(VARIABLES.DATETIME_FORMAT))] \
        .groupby('tickersymbol') \
        .agg(last_buy_signal=('timestamp', 'max'))

    # Following ensures that day datetime string representation has limited information for sanity
    last_buy_signal_df['last_buy_signal'] = last_buy_signal_df['last_buy_signal'].replace('T00:00:00', '', regex=True)
    last_buy_signal_df['last_buy_signal'] = last_buy_signal_df['last_buy_signal'].replace('\+0530', '', regex=True)

    agg_df = final_df.groupby('tickersymbol').agg({
        'close': ['min', 'mean', 'last'],
        'macd': ['last'],
        'signal': ['last'],
        'rsi': ['last']
    })
    agg_df['close_last_by_min'] = round((agg_df['close']['last'] - agg_df['close']['min']) / agg_df['close']['last'] * 100, 2)
    agg_df['close_last_by_avg'] = round((agg_df['close']['last'] - agg_df['close']['mean']) / agg_df['close']['last'] * 100, 2)

    agg_df = agg_df.join(last_buy_signal_df, on='tickersymbol', how='left')

    return agg_df
