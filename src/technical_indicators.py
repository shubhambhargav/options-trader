import emoji
import numpy as np
import pandas as pd


def add_recommendations(option_df):
    recommendations = option_df[
        (option_df['close_last_by_avg'] < 5) &
            (option_df['close_last_by_avg'] > -10) &
            (option_df['%_dip'] >= 8)
    ].groupby('instrument').first()
    recommendations['recommendation'] = ':white_check_mark:'

    option_df = pd.merge(
        option_df.set_index(['margin__tradingsymbol', 'strike']),
        recommendations[['margin__tradingsymbol', 'strike', 'recommendation']],
        how='left',
        on=['margin__tradingsymbol', 'strike']
    )
    option_df['recommendation'] = option_df['recommendation'] \
        .replace(np.nan, 'NA') \
        .apply(lambda x: emoji.emojize(x, use_aliases=True))

    return option_df
