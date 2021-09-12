import json

# Runtime variables
OPTIONS_OF_INTEREST = [
    # Indices
    { 'ticker': 'NIFTY', 'custom_filters': { 'minimum_dip': 2 } },
    # Public sector
    { 'ticker': 'COALINDIA' },
    # Banking & Finance
    { 'ticker': 'ICICIBANK' },
    { 'ticker': 'IDFCFIRSTB' },
    { 'ticker': 'HDFC', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'M&MFIN' },
    { 'ticker': 'KOTAKBANK'},
    { 'ticker': 'BANDHANBNK' },
    # Consumer goods / manufacturing
    { 'ticker': 'HEROMOTOCO' },
    { 'ticker': 'HINDUNILVR', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'MARUTI' },
    { 'ticker': 'NESTLEIND' },
    # Uncategorized
    { 'ticker': 'DRREDDY' },
    { 'ticker': 'TATACHEM' },
    { 'ticker': 'RELIANCE' },
    { 'ticker': 'BHARTIARTL' },
    { 'ticker': 'PVR' },
    # Tech
    { 'ticker': 'INFY', 'custom_filters': { 'minimum_dip': 3 } },
    { 'ticker': 'NAUKRI' },
    { 'ticker': 'COFORGE' },
    { 'ticker': 'MINDTREE' },
    { 'ticker': 'LTI' },
    { 'ticker': 'HCLTECH' },
]
CONFIG = json.loads(open('./config.json').read())
