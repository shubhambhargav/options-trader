from datetime import datetime, timedelta
import numpy as np

import pandas as pd
import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc

TIMESTAMP_FORMAT = '%Y-%m-%d'


class TechnicalIndicatorsController:
    @staticmethod
    def add_momentum_indicators(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        # Adding MACD indicators
        exp1 = df[column_name].ewm(span=12, adjust=False).mean()
        exp2 = df[column_name].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()

        df['macd'] = macd
        df['signal'] = signal

        # Adding RSI indicator
        delta = df[column_name].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down

        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    @staticmethod
    def get_buy_signal(df: pd.DataFrame) -> pd.DataFrame:
        df['buy_signal'] = 0

        df.loc[
            df['macd'].shift(1).gt(df['signal'].shift(1)) &
                df['macd'].shift(2).gt(df['signal'].shift(2)) &
                df['macd'].shift(3).gt(df['signal'].shift(3)),
            'buy_signal'
        ] = 1

        df.loc[
            df['buy_signal'].shift(1).eq(1) &
                df['buy_signal'].shift(2).eq(1) &
                df['buy_signal'].shift(3).eq(0),
            'buy_signal'
        ] = 2

        agg_df = df[(df['buy_signal'] == 2) & (df['timestamp'] >= (datetime.now() - timedelta(days=30)).strftime(TIMESTAMP_FORMAT))] \
            .groupby('tickersymbol') \
            .agg(last_buy_signal=('timestamp', 'max')) \
            .reset_index()

        # Following ensures that day datetime string representation has limited information for sanity
        agg_df['last_buy_signal'] = agg_df['last_buy_signal'].replace('T00:00:00', '', regex=True)
        agg_df['last_buy_signal'] = agg_df['last_buy_signal'].replace('\+0530', '', regex=True)

        return agg_df

    @staticmethod
    def get_support_and_resistance(df: pd.DataFrame, low_column_name: str = 'low', high_column_name: str = 'high', is_print_enabled: bool = False):
        # Ref: https://towardsdatascience.com/detection-of-price-support-and-resistance-levels-in-python-baedc44c34c9
        average_candle_size = np.mean(df[high_column_name] - df[low_column_name])
        levels = []

        def is_support(df, i):
            support = df[low_column_name][i] < df[low_column_name][i - 1] and \
                df[low_column_name][i] < df[low_column_name][i + 1] and \
                df[low_column_name][i + 1] < df[low_column_name][i + 2] and \
                df[low_column_name][i - 1] < df[low_column_name][i - 2]

            return support

        def is_resistance(df, i):
            resistance = df[high_column_name][i] > df[high_column_name][i - 1] and \
                df[high_column_name][i] > df[high_column_name][i + 1] and \
                df[high_column_name][i + 1] > df[high_column_name][i + 2] and \
                df[high_column_name][i - 1] > df[high_column_name][i - 2]

            return resistance

        def is_far_from_level(l):
            return np.sum([abs(l - x) < average_candle_size for x in levels]) == 0

        for i in range(2, df.shape[0] - 2):
            if is_support(df, i):
                l = df[low_column_name][i]

                if is_far_from_level(l):
                    levels.append((i, l))
            elif is_resistance(df, i):
                l = df[high_column_name][i]

                if is_far_from_level(l):
                    levels.append((i, l))

        def plot_all():
            fig, ax = plt.subplots()

            new_df = df.copy()

            new_df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%dT%H:%M:%S+0530')

            new_df['timestamp'] = new_df['timestamp'].apply(mpl_dates.date2num)

            candlestick_ohlc(
                ax, new_df.values, width=0.6, \
                colorup='green', colordown='red', alpha=0.8
            )
            date_format = mpl_dates.DateFormatter('%d %b %Y')
            ax.xaxis.set_major_formatter(date_format)
            fig.autofmt_xdate()
            fig.tight_layout()
            for level in levels:
                plt.hlines(
                    level[1], xmin=new_df['timestamp'][level[0]], \
                    xmax=max(new_df['timestamp']), colors='blue'
                )
            fig.show()

        if is_print_enabled:
            plot_all()

        return levels
