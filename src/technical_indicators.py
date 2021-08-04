

def add_indicators(instrument_df):
    # Adding MACD indicators
    exp1 = instrument_df.close.ewm(span=12, adjust=False).mean()
    exp2 = instrument_df.close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()

    instrument_df['macd'] = macd
    instrument_df['signal'] = signal
    
    # Adding RSI indicator
    delta = instrument_df['close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down

    instrument_df['rsi'] = 100 - (100 / (1 + rs))
    
    return instrument_df


def add_buying_signal(instrument_df):
    instrument_df['buy_signal'] = 0
    
    instrument_df.loc[
        instrument_df['macd'].shift(1).gt(instrument_df['signal'].shift(1)) &
            instrument_df['macd'].shift(2).gt(instrument_df['signal'].shift(2)) &
            instrument_df['macd'].shift(3).gt(instrument_df['signal'].shift(3)),
        'buy_signal'
    ] = 1

    instrument_df.loc[
        instrument_df['buy_signal'].shift(1).eq(1) &
            instrument_df['buy_signal'].shift(2).eq(1) &
            instrument_df['buy_signal'].shift(3).eq(0),
        'buy_signal'
    ] = 2
    
    return instrument_df