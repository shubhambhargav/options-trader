

# Singleton class
class VARIABLES:
    # Runtime variables
    DATETIME_FORMAT = '%Y-%m-%d'
    MAX_TIME_TO_EXPIRY = 40  # in days
    MINIMUM_PROFIT_PERCENTAGE = 2  # in percentage
    TARGET = -90  # in percentage i.e. recovering the entire put amount
    STOPLOSS = 250 # in percentage i.e. only holding till 250 % drop
    MINIMUM_MARGIN_FOR_ANY_PURCHASE = 50000  # in INR
