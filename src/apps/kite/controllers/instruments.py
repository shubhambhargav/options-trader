from dataclasses import asdict
import json
from typing import List
from datetime import date, datetime, timedelta
from pandas.core.frame import DataFrame

import requests
import pandas as pd
from dacite import from_dict

from .users import UsersController

import src.utilities as Utilities
from src.cache import Cache
from src.apps.nse.controllers.options import OptionsController as HistoricalOptionalsController
from src.apps.settings.controllers import ConfigController

from ..models import InstrumentModel, EnrichedInstrumentModel, CandleModel, OptionModel, StockOfInterest
from .technicals import TechnicalIndicatorsController

KITE_AUTH_TOKEN = ConfigController.get_config().kite_auth_token


class InstrumentsController:
    INSTRUMENT_TOKEN_DICT = None

    @staticmethod
    def get_instrument_token_dict() -> dict:
        # Since instrument token don't change often, we are caching them for subsequent calls
        if InstrumentsController.INSTRUMENT_TOKEN_DICT:
            return InstrumentsController.INSTRUMENT_TOKEN_DICT

        response = requests.get('https://api.kite.trade/instruments')

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        instruments = Utilities.csv_text_to_dict(response.text)
        instrument_token_dict = {}

        for instrument in instruments:
            instrument_token_dict[instrument['tradingsymbol']] = instrument['instrument_token']

        InstrumentsController.INSTRUMENT_TOKEN_DICT = instrument_token_dict

        return instrument_token_dict

    @Cache
    @staticmethod
    def get_instrument(tickersymbol: str, on_date: date = None) -> InstrumentModel:
        """Legacy function from options module"""
        # TODO: Possibly retire this function
        response = requests.post(
            'https://api.sensibull.com/v1/instrument_details',
            headers={
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'underlyings': [tickersymbol]
            })
        )

        if response.status_code != 200:
            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        data = response.json()

        if not data.get(tickersymbol):
            raise Exception('No options getting traded for %s' % tickersymbol)

        # Response contains instrument ID as a key, hence to maintain the sanity of the function
        # the response enusures that we are only sending the respective instrument details
        instrument = json.loads(list(data.values())[0])

        instrument['tickersymbol'] = tickersymbol

        instrument = from_dict(data_class=InstrumentModel, data=instrument)

        if on_date:
            instrument.last_price = InstrumentsController.get_instrument_price_details(
                tickersymbol=instrument.tickersymbol,
                on_date=on_date
            ).close

        return instrument

    @Cache
    @staticmethod
    def get_instrument_price_details(tickersymbol: str, on_date: date) -> CandleModel:
        candles = InstrumentsController.get_instrument_candles(
            tickersymbol=tickersymbol,
            from_date=on_date,
            to_date=on_date
        )

        return candles[0]

    @staticmethod
    def get_instrument_candles(tickersymbol: str, from_date: date = None, to_date: date = None) -> List[CandleModel]:
        insturment_token_dict = InstrumentsController.get_instrument_token_dict()

        # Following is documented here: https://kite.trade/docs/connect/v3/historical/
        response_headers = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        tickersymbol_backup = {
            'BANKNIFTY': '260105',
            'NIFTY': '256265'
        }

        if not from_date:
            from_date = datetime.now() - timedelta(days=365)

        if not to_date:
            to_date = datetime.now()

        instrument_token = insturment_token_dict[tickersymbol] if tickersymbol in insturment_token_dict else tickersymbol_backup[tickersymbol]

        response = requests.get(
            'https://kite.zerodha.com/oms/instruments/historical/%(instrument_token)s/day?user_id=%(user_id)s&oi=1&from=%(from)s&to=%(to)s' % {
                'instrument_token': instrument_token,
                'user_id': UsersController.get_current_user().user_id,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d')
            },
            headers={
                'Authorization': f'enctoken {KITE_AUTH_TOKEN}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        instrument_candles = []

        for row in response.json()['data']['candles']:
            instrument_candles.append(from_dict(data_class=CandleModel, data=dict(zip(response_headers, row))))

        return instrument_candles

    @staticmethod
    def get_options_chain(instrument: InstrumentModel, on_date: date = None) -> List[OptionModel]:
        response = requests.get(
            'https://api.sensibull.com/v1/instruments/%s' % instrument.tickersymbol
        )

        if response.status_code != 200:
            raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

        if on_date:
            return HistoricalOptionalsController.get_historical_data(
                tickersymbol=instrument.tickersymbol,
                expiry_date=Utilities.get_last_thursday_for_derivative(dt=on_date + timedelta(days=30)),
                from_date=on_date,
                to_date=on_date
            )

        return [from_dict(data_class=OptionModel, data=option) for option in response.json()['data']]

    @Cache
    @staticmethod
    def enrich_instruments(instruments: List[StockOfInterest], on_date: date = None) -> List[EnrichedInstrumentModel]:
        candles_df = pd.DataFrame()
        support_resistance_dict = {}

        for instrument in instruments:
            candles = InstrumentsController.get_instrument_candles(
                tickersymbol=instrument.tickersymbol,
                from_date=on_date - timedelta(days=365) if on_date else None,
                to_date=on_date if on_date else None
            )
            candles_df = pd.DataFrame.from_dict(data=[asdict(candle) for candle in candles])

            support_and_resistance = TechnicalIndicatorsController.get_support_and_resistance(df=candles_df)

            if support_and_resistance:
                # TODO: Make the following more readable
                # it's the last price where support/resistance was found
                if support_and_resistance[-1][1] > candles[-1].close:
                    support_resistance_dict[instrument.tickersymbol] = {
                        'last_support': support_and_resistance[-1][1],
                        'last_resistance': support_and_resistance[-2][1]
                    }
                else:
                    support_resistance_dict[instrument.tickersymbol] = {
                        'last_support': support_and_resistance[-2][1],
                        'last_resistance': support_and_resistance[-1][1]
                    }

            candles = [{**asdict(candle), **asdict(instrument)} for candle in candles]
            instrument_candles_df = pd.DataFrame.from_dict(data=candles)

            instrument_candles_df = TechnicalIndicatorsController.add_momentum_indicators(df=instrument_candles_df, column_name='close')

            if candles_df.empty:
                candles_df = instrument_candles_df

                continue

            candles_df = pd.concat([candles_df, instrument_candles_df])

        last_buy_signal_df = TechnicalIndicatorsController.get_buy_signal(df=candles_df)

        enriched_instrument_df = candles_df.groupby('tickersymbol').agg(
            close_min=('close', 'min'),
            close_mean=('close', 'mean'),
            close_last=('close', 'last'),
            macd_last=('macd', 'last'),
            signal_last=('signal', 'last'),
            rsi_last=('rsi', 'last')
        )

        enriched_instrument_df['close_last_by_min'] = round(
            (enriched_instrument_df['close_last'] - enriched_instrument_df['close_min']) /
                enriched_instrument_df['close_last'] * 100,
            2
        )
        enriched_instrument_df['close_last_by_avg'] = round(
            (enriched_instrument_df['close_last'] - enriched_instrument_df['close_mean']) /
                enriched_instrument_df['close_last'] * 100,
            2
        )

        enriched_instrument_df = enriched_instrument_df \
            .join(last_buy_signal_df.set_index('tickersymbol'), on='tickersymbol', how='left') \
            .reset_index()

        enriched_instrument_df['last_support'] = enriched_instrument_df['tickersymbol'].apply(lambda x: support_resistance_dict[x]['last_support'])
        enriched_instrument_df['last_resistance'] = enriched_instrument_df['tickersymbol'].apply(lambda x: support_resistance_dict[x]['last_resistance'])

        enriched_instrument_df['close_last_by_support'] = round(
            (enriched_instrument_df['close_last'] - enriched_instrument_df['last_support']) /
                enriched_instrument_df['close_last'] * 100,
            2
        )
        enriched_instrument_df['close_last_by_resistance'] = round(
            (enriched_instrument_df['close_last'] - enriched_instrument_df['last_resistance']) /
                enriched_instrument_df['close_last'] * 100,
            2
        )

        return [from_dict(data_class=EnrichedInstrumentModel, data=instrument) for instrument in enriched_instrument_df.to_dict('records')]
