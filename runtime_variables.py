import json

# Runtime variables
OPTIONS_OF_INTEREST = [
    { 'ticker': 'MARUTI' },
    { 'ticker': 'INFY' },
    { 'ticker': 'COALINDIA' },
    { 'ticker': 'ICICIBANK' },
    { 'ticker': 'IDFCFIRSTB' },
    { 'ticker': 'HEROMOTOCO' },
    { 'ticker': 'HINDUNILVR' },
    { 'ticker': 'NAUKRI' },
    { 'ticker': 'RELIANCE' },
    { 'ticker': 'NESTLEIND' },
    { 'ticker': 'HDFC' },
    # { 'ticker': 'BANDHANBNK' },
    { 'ticker': 'DRREDDY' },
    # { 'ticker': 'PVR' },
    { 'ticker': 'BHARTIARTL' },
    { 'ticker': 'KOTAKBANK' },
    { 'ticker': 'M&MFIN' },
    { 'ticker': 'TATACHEM' },
]
CONFIG = json.loads(open('./config.json').read())
