import requests
from dataclasses import asdict

from datetime import date, timedelta
from typing import List
import pandas as pd

from dacite import from_dict
from src.apps.settings.controllers import ConfigController
from src.logger import LOGGER
from src.apps.kite.controllers import TechnicalIndicatorsController

from ..models import CandleModel, SymbolModel, SymbolBaseModel, EnrichedSymbolModel
from ..client import QuestradeClient

Q = QuestradeClient().initialize()


class SymbolsController:
    @staticmethod
    def get_candles(symbol_id: str, start: date, end: date, interval: str = 'OneDay') -> List[CandleModel]:
        candles_response = Q.markets_candles(
            id=symbol_id, startTime=start.strftime('%Y-%m-%dT00:00:00-05:00'),
            endTime=end.strftime('%Y-%m-%dT00:00:00-05:00'), interval=interval
        )

        candles: List[CandleModel] = []

        for row in candles_response['candles']:
            candles.append(from_dict(data_class=CandleModel, data=row))

        return candles

    @staticmethod
    def get_symbols(ids: list = [], names: list = []) -> List[SymbolModel]:
        if not ids and not names:
            raise ValueError('Either ids or names must be provided')

        values = ids if ids else names

        response = requests.get(
            'https://api01.iq.questrade.com/v1/symbols?%(param)s=%(value)s' % {
                'param': 'ids' if ids else 'names',
                'value': ','.join([str(val) for val in values])
            },
            headers={
                'Authorization': f'Bearer {ConfigController.get_config().questrade_access_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        symbols: List[CandleModel] = []

        for row in response.json()['symbols']:
            symbols.append(from_dict(data_class=SymbolModel, data=row))

        return symbols

    @staticmethod
    def find_symbol(name: str) -> SymbolBaseModel:
        symbol = Q.symbols_search(prefix=name)['symbols'][0]

        return from_dict(data_class=SymbolBaseModel, data=symbol)

    @staticmethod
    def get_symbol(id: int) -> SymbolModel:
        symbol = Q.symbol(id)['symbols'][0]

        return from_dict(data_class=SymbolModel, data=symbol)

    @staticmethod
    def enrich_symbols(symbols: List[SymbolModel]) -> List[EnrichedSymbolModel]:
        candles_df = pd.DataFrame()
        support_resistance_dict = {}
        today = date.today()

        for symbol in symbols:
            candles = SymbolsController.get_candles(
                symbol_id=symbol.symbolId,
                start=(today - timedelta(days=365)),
                end=today,
                interval='OneDay'
            )

            symbol_candles_df = pd.DataFrame.from_dict(data=[asdict(candle) for candle in candles])

            support_and_resistance = TechnicalIndicatorsController.get_support_and_resistance(
                df=symbol_candles_df,
                low_column_name='low',
                high_column_name='high',
                timestamp_column_name='start',
                timestamp_format='%Y-%m-%dT%H:%M:%S.%f%z'
            )

            if support_and_resistance:
                support_resistance_dict[symbol.symbol] = {
                    'supports': [elem[2] for elem in support_and_resistance if elem[1] == -1],
                    'resistances': [elem[2] for elem in support_and_resistance if elem[1] == 1],
                }

            candles = [{**asdict(candle), **asdict(symbol)} for candle in candles]
            symbol_candles_df = pd.DataFrame.from_dict(data=candles)

            symbol_candles_df = TechnicalIndicatorsController.add_momentum_indicators(df=symbol_candles_df, column_name='close')

            if candles_df.empty:
                candles_df = symbol_candles_df

                continue

            candles_df = pd.concat([candles_df, symbol_candles_df])

        last_buy_signal_df = TechnicalIndicatorsController.get_buy_signal(
            df=candles_df, symbol_column_name='symbol', timestamp_column_name='start'
        )

        enriched_symbol_df = candles_df.groupby('symbol').agg(
            close_min=('close', 'min'),
            close_mean=('close', 'mean'),
            close_last=('close', 'last'),
            macd_last=('macd', 'last'),
            signal_last=('signal', 'last'),
            rsi_last=('rsi', 'last')
        )

        enriched_symbol_df['close_last_by_min'] = round(
            (enriched_symbol_df['close_last'] - enriched_symbol_df['close_min']) /
                enriched_symbol_df['close_last'] * 100,
            2
        )
        enriched_symbol_df['close_last_by_avg'] = round(
            (enriched_symbol_df['close_last'] - enriched_symbol_df['close_mean']) /
                enriched_symbol_df['close_last'] * 100,
            2
        )

        enriched_symbol_df = enriched_symbol_df \
            .join(last_buy_signal_df.set_index('symbol'), on='symbol', how='left') \
            .reset_index()

        enriched_symbol_df['last_support'] = enriched_symbol_df['symbol'] \
            .apply(
                lambda x: support_resistance_dict[x]['supports'][-1] if support_resistance_dict[x]['supports'] else None
            )
        enriched_symbol_df['last_resistance'] = enriched_symbol_df['symbol'] \
            .apply(
                lambda x: support_resistance_dict[x]['resistances'][-1] if support_resistance_dict[x]['resistances'] else None
            )

        enriched_symbol_df['close_last_by_support'] = enriched_symbol_df \
            .apply(
                lambda x: None if x.last_support is None \
                    else round((x.close_last - x.last_support) / x.close_last * 100, 2),
                axis=1
            )
        enriched_symbol_df['close_last_by_resistance'] = enriched_symbol_df \
            .apply(
                lambda x: None if x.last_resistance is None \
                    else round((x.close_last - x.last_resistance) / x.close_last * 100, 2),
                axis=1
            )

        return [from_dict(data_class=EnrichedSymbolModel, data=symbol) for symbol in enriched_symbol_df.to_dict('records')]
