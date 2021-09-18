import json

# Runtime variables
OPTIONS_OF_INTEREST = [
    # Public sector
    { 'tickersymbol': 'COALINDIA' },
    # Banking & Finance
    { 'tickersymbol': 'ICICIBANK' },
    { 'tickersymbol': 'IDFCFIRSTB' },
    { 'tickersymbol': 'HDFCBANK', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'M&MFIN' },
    { 'tickersymbol': 'KOTAKBANK'},
    { 'tickersymbol': 'BANDHANBNK' },
    # Insurance
    { 'tickersymbol': 'HDFCLIFE', 'custom_filters': { 'minimum_dip': 3 } },
    # Consumer goods / manufacturing
    { 'tickersymbol': 'HEROMOTOCO' },
    { 'tickersymbol': 'TITAN', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'PIDILITIND', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'ASIANPAINT', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'MRF', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'HINDUNILVR', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'MARUTI' },
    { 'tickersymbol': 'NESTLEIND' },
    # AMC - Emerging Market
    { 'tickersymbol': 'HDFCAMC', 'custom_filters': { 'minimum_dip': 3 } },
    # Uncategorized
    { 'tickersymbol': 'HDFC' },
    { 'tickersymbol': 'DRREDDY' },
    { 'tickersymbol': 'TATACHEM' },
    { 'tickersymbol': 'RELIANCE', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'BHARTIARTL' },
    { 'tickersymbol': 'PVR' },
    { 'tickersymbol': 'ITC', 'custom_filters': { 'minimum_dip': 3 } },
    # Tech
    { 'tickersymbol': 'INFY', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'TCS', 'custom_filters': { 'minimum_dip': 3 } },
    { 'tickersymbol': 'NAUKRI' },
    { 'tickersymbol': 'COFORGE' },
    { 'tickersymbol': 'MINDTREE' },
    { 'tickersymbol': 'LTI' },
    { 'tickersymbol': 'HCLTECH' },
]
CONFIG = json.loads(open('./config.json').read())
