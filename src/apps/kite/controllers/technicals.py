from datetime import datetime, timedelta

import pandas as pd

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
