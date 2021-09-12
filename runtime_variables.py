import json

# Runtime variables
OPTIONS_OF_INTEREST = [
    # Indices
    # { 'ticker': 'NIFTY' },
    # Public sector
    { 'ticker': 'COALINDIA' },
    # Banking & Finance
    { 'ticker': 'ICICIBANK' },
    { 'ticker': 'IDFCFIRSTB' },
    { 'ticker': 'HDFC' },
    { 'ticker': 'M&MFIN' },
    { 'ticker': 'KOTAKBANK' },
    # { 'ticker': 'BANDHANBNK' },
    # Consumer goods / manufacturing
    { 'ticker': 'HEROMOTOCO' },
    { 'ticker': 'HINDUNILVR' },
    { 'ticker': 'MARUTI' },
    { 'ticker': 'NESTLEIND' },
    # Uncategorized
    { 'ticker': 'DRREDDY' },
    { 'ticker': 'TATACHEM' },
    { 'ticker': 'RELIANCE' },
    { 'ticker': 'BHARTIARTL' },
    # { 'ticker': 'PVR' },
    # Tech
    { 'ticker': 'INFY' },
    { 'ticker': 'NAUKRI' },
    { 'ticker': 'COFORGE' },
    { 'ticker': 'MINDTREE' },
    { 'ticker': 'LTI' },
    { 'ticker': 'HCLTECH' },
]
CONFIG = json.loads(open('./config.json').read())
