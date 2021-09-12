import json

# Singleton class
class VARIABLES:
    # Runtime variables
    DATETIME_FORMAT = '%Y-%m-%d'
    MAX_TIME_TO_EXPIRY = 40  # in days
    MINIMUM_PROFIT_PERCENTAGE = 2  # in percentage
    TARGET = -90  # in percentage i.e. recovering the entire put amount
    STOPLOSS = 250 # in percentage i.e. only holding till 250 % drop
    MINIMUM_MARGIN_FOR_ANY_PURCHASE = 50000  # in INR
    PE_OPTIONS_OF_INTEREST_THRESHOLD = {
        'min': 5,  # 0.5
        'max': 20  # 10
    }  # in percentage points
    CONFIG = json.loads(open('./config.json').read())


def reload():
    VARIABLES.CONFIG = json.loads(open('./config.json').read())
