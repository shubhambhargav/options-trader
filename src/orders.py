import requests

from ._variables import VARIABLES
from . import utilities as Utilities
from . import options


def place_order(option: dict):
    # Since the price of the option can change during the analysis,
    # following code ensures that we don't trade at a lower value than the last price
    option_last_price = options.get_option_last_price(tradingsymbol=option['name'], underlying_instrument=option['instrument'])
    expected_trade_price = option['last_price']

    if option_last_price > expected_trade_price:
        print(
            'Increasing the trade price for %s. Previous price: %s, new price: %s' % (
                option['name'], expected_trade_price, option_last_price
            )
        )
        print('New expected profit: %s' % (expected_trade_price * int(option['lot_size'])))

        expected_trade_price = option_last_price

    data = {
      'variety': 'regular',
      'exchange': 'NFO',
      'tradingsymbol': option['name'],
      'transaction_type': 'SELL',
      'order_type': 'LIMIT',
      'quantity': int(option['lot_size']),
      'price': Utilities.round_nearest(number=expected_trade_price + 0.09, unit=0.05),
      'product': 'NRML',
      'validity': 'DAY',
      'disclosed_quantity': '0',
      'trigger_price': '0',
      'squareoff': '0',
      'stoploss': '0',
      'trailing_stoploss': '0',
      'user_id': VARIABLES.CONFIG['user_id'],
      'gtt_params': '[[0,%s],[0,%s]]' % (VARIABLES.TARGET, VARIABLES.STOPLOSS)
    }

    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
    }
    
    response = requests.post(
        'https://kite.zerodha.com/oms/orders/regular',
        headers=headers,
        data=data
    )
    
    if response.status_code == 200:
        print('Successfully placed the order for %s' % option['name'])
        
        return

    print('Unexpected response code got from Kite while placing the order: %d, error: %s' % (response.status_code, response.text))
