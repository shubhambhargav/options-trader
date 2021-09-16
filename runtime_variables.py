import json

# Runtime variables
OPTIONS_OF_INTEREST = [
    # Public sector
    { 'ticker': 'COALINDIA' },
    # Banking & Finance
    { 'ticker': 'ICICIBANK' },
    { 'ticker': 'IDFCFIRSTB' },
    { 'ticker': 'HDFCBANK', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'M&MFIN' },
    { 'ticker': 'KOTAKBANK'},
    { 'ticker': 'BANDHANBNK' },
    # Insurance
    { 'ticker': 'HDFCLIFE', 'custom_filters': { 'minimum_dip': 3 } },
    # Consumer goods / manufacturing
    { 'ticker': 'HEROMOTOCO' },
    { 'ticker': 'TITAN', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'PIDILITIND', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'ASIANPAINT', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'MRF', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'HINDUNILVR', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'MARUTI' },
    { 'ticker': 'NESTLEIND' },
    # AMC - Emerging Market
    { 'ticker': 'HDFCAMC', 'custom_filters': { 'minimum_dip': 3 } },
    # Uncategorized
    { 'ticker': 'HDFC' },
    { 'ticker': 'DRREDDY' },
    { 'ticker': 'TATACHEM' },
    { 'ticker': 'RELIANCE', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'BHARTIARTL' },
    { 'ticker': 'PVR' },
    { 'ticker': 'ITC', 'custom_filters': { 'minimum_dip': 3 } },
    # Tech
    { 'ticker': 'INFY', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'TCS', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'NAUKRI' },
    { 'ticker': 'COFORGE' },
    { 'ticker': 'MINDTREE' },
    { 'ticker': 'LTI' },
    { 'ticker': 'HCLTECH' },
]
# OPTIONS_OF_INTEREST = [
#     { 'ticker': 'PVR', 'custom_filters': { 'minimum_dip': 3 } },
#     # { 'ticker': 'HCLTECH' },
# ]
CONFIG = json.loads(open('./config.json').read())
