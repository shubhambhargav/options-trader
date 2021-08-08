from datetime import datetime, timedelta

import requests
import pandas as pd

from . import utilities as Utilities
from ._variables import VARIABLES
from . import technical_indicators

INSTRUMENT_TOKEN_DICT = {}


def get_instrument_token_dict():
    global INSTRUMENT_TOKEN_DICT

    if INSTRUMENT_TOKEN_DICT:
        return INSTRUMENT_TOKEN_DICT

    response = requests.get('https://api.kite.trade/instruments')
    
    if response.status_code != 200:
        raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))
    
    instruments = Utilities.csv_text_to_dict(response.text)
    instrument_token_dict = {}

    for instrument in instruments:
        instrument_token_dict[instrument['tradingsymbol']] = instrument['instrument_token']

    # Caching the response
    # TODO: Maybe look for alternate implementation here
    INSTRUMENT_TOKEN_DICT = instrument_token_dict

    return instrument_token_dict


def get_instrument_data(tickersymbol: str):
    insturment_token_dict = get_instrument_token_dict()
    config = VARIABLES.CONFIG

    # Following is documented here: https://kite.trade/docs/connect/v3/historical/
    response_headers = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    tickersymbol_backup = {
        'BANKNIFTY': 'NIFTY BANK'
    }
    
    instrument_token = insturment_token_dict[tickersymbol] if tickersymbol in insturment_token_dict else tickersymbol_backup[tickersymbol]
    
    response = requests.get(
        'https://kite.zerodha.com/oms/instruments/historical/%(instrument_token)s/day?user_id=%(user_id)s&oi=1&from=%(from)s&to=%(to)s' % {
            'instrument_token': instrument_token,
            'user_id': config['user_id'],
            'from': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            'to': datetime.now().strftime('%Y-%m-%d')
        },
        headers={
            'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
        }
    )

    if response.status_code != 200:
        raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))
        
    instrument_data = []
        
    for row in response.json()['data']['candles']:
        instrument_data.append(dict(zip(response_headers, row)))
        
    return instrument_data


def _get_enriched_instrument_df(tickersymbol: str):
    instrument_data = get_instrument_data(tickersymbol=tickersymbol)
    
    instrument_df = pd.DataFrame.from_dict(data=instrument_data)
    
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
