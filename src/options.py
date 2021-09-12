import json
import pandas as pd
from typing import List
from copy import deepcopy
from datetime import datetime, timedelta
from multiprocessing import Pool

import requests

try:
    from ._variables import VARIABLES
    from . import utilities as Utilities
    from . import models
    from .instruments import get_instrument_details
except:
    # In order to run the module in isolation, following is required
    # This enables local testing
    from _variables import VARIABLES
    import utilities as Utilities


def get_time_to_expiry_in_days(option: dict):
    expiry = datetime.strptime(option['expiry'], VARIABLES.DATETIME_FORMAT)
    today = datetime.now()

    return (expiry - today).days


def _get_full_option_chain(instrument_id: str):
    response = requests.get(
        'https://api.sensibull.com/v1/instruments/%s' % instrument_id
    )

    if response.status_code != 200:
        raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

    return response.json()['data']


def _get_option_margin_bulk(options: dict) -> List[models.OptionMargin]:
    # Note: Hard-coded for options and SELL type for now
    # TODO: Possibly change to leverage BUY as well
    data = []
    chunk_size = 100
    return_data = []

    for option in options:
        data.append({
            'exchange': 'NFO',
            'tradingsymbol': option['tradingsymbol'],
            'transaction_type': 'SELL',
            'product': 'NRML',
            'variety': 'regular',
            'order_type': 'LIMIT',
            'quantity': int(option['lot_size']) if option['lot_size'].is_integer() else option['lot_size'],
            'price': option['last_price']
        })

    for chunk in Utilities.divide_chunks(input_list=data, chunk_size=chunk_size):
        response = requests.post(
            'https://kite.zerodha.com/oms/margins/orders',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
            },
            data=json.dumps(chunk)
        )

        if response.status_code != 200:
            raise Exception('Invalid response code found: %s, expected: 200, response: %s' % (response.status_code, response.text))

        return_data += response.json()['data']

    return return_data


def get_instrument_options_of_interest(options: list, instrument: dict, custom_filters: models.StockCustomFilters):
    instrument_price = instrument['last_price']
    selected_options = []

    for option in options:
        if option['instrument_type'] != 'PE':  # only interested in PE options right now
            continue

        if option['strike'] > instrument_price:  # only interested in valid PE i.e. less price than instrument_price
            continue

        if get_time_to_expiry_in_days(option=option) > VARIABLES.MAX_TIME_TO_EXPIRY:  # only looking for options within next X numeber of days
            continue

        percentage_dip = (instrument_price - option['strike']) / instrument_price * 100

        if custom_filters.minimum_dip < percentage_dip < custom_filters.maximum_dip:
            option['percentage_dip'] = percentage_dip

            selected_options.append(option)

    return selected_options


def get_margin():
    response = requests.get(
        'https://kite.zerodha.com/oms/user/margins',
        headers={
            'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}",
            'Content-Type': 'application/json'
        }
    )

    if response.status_code != 200:
        raise Exception('Invalid response code found: %s, expected: 200' % response.status_code)

    return response.json()['data']['equity']['net']


def _enrich_options(options: List[models.Option]) -> List[models.ProcessedOption]:
    enriched_options = []
    margin_data = _get_option_margin_bulk(options=options)

    # Following is used to avoid multiple calls to the underlying
    # instrument API
    instrument_data_cache = {}

    for iteration, option in enumerate(options):
        option = models.ProcessedOption(**option)

        option.backup_money = option.strike * option.lot_size
        option.margin = models.OptionMargin(**margin_data[iteration])

        if option.underlying_instrument in instrument_data_cache:
            option.instrument_data = instrument_data_cache[option.underlying_instrument]
        else:
            instrument_data = get_instrument_details(instrument_id=option.underlying_instrument)
            option.instrument_data = models.Instrument(**instrument_data)

            instrument_data_cache[option.underlying_instrument] = instrument_data


        profit = option.last_price * option.lot_size
        option.profit = models.OptionProfit(**{
            'value': profit,
            'percentage': (profit / option.margin.total) * 100
        })

        enriched_options.append(option)

    return enriched_options


def get_options_of_interest(stocks: List[models.StockOfInterest]) -> List[models.ProcessedOption]:
    all_options = []

    for stock in stocks:
        # Following is a hack in the absence of rendering the incoming subclass dict into
        # a dataclass. TODO: Find the right way of doing it
        custom_filters = None

        if stock.get('custom_filters'):
            custom_filters = models.StockCustomFilters(**stock['custom_filters'])

        stock = models.StockOfInterest(**stock)

        if custom_filters:
            stock.custom_filters = custom_filters

        instrument = get_instrument_details(instrument_id=stock.ticker)
        options = _get_full_option_chain(instrument_id=stock.ticker)

        options_of_interest = get_instrument_options_of_interest(
            options=options, instrument=instrument, custom_filters=stock.custom_filters
        )
        options_of_interest = _enrich_options(options=options_of_interest)

        all_options += options_of_interest

        print('Processed for %s' % stock.ticker)

    all_options = list(filter(
        lambda elem: elem.profit.percentage >= VARIABLES.MINIMUM_PROFIT_PERCENTAGE,
        sorted(
            all_options, key=lambda x: x.profit.percentage + x.percentage_dip, reverse=True
        )
    ))

    for seq_no in range(len(all_options)):
        all_options[seq_no].sequence_id = seq_no + 1

    return all_options


def get_options_of_interest_df(stocks: List[models.StockOfInterest]) -> models.ProcessedOptions:
    options_of_interest = get_options_of_interest(stocks=stocks)

    flattened_options_of_interest = Utilities.dict_array_to_df(
        dict_array=[option.__dict__ for option in options_of_interest]
    )

    df = pd.DataFrame(flattened_options_of_interest)

    if len(df) == 0:
        return df

    return df


def get_option_last_price(tradingsymbol: str, underlying_instrument: str) -> float:
    option_chain = _get_full_option_chain(instrument_id=underlying_instrument)

    for option in option_chain:
        if option['tradingsymbol'] == tradingsymbol:
            return option['last_price']

    return None


def select_options(options: list, selection: str):
    option_dict = dict((option['seq'], option) for option in options)
    selected_options = []
    expected_info = {
        'profit': 0,
        'margin': 0
    }

    for selected in selection.split(','):
        option = option_dict[int(selected)]

        selected_options.append(option)

        expected_info['profit'] += option['profit']
        expected_info['margin'] += option['margin']

    print('Expected profit: %d, margin: %d' % (expected_info['profit'], expected_info['margin']))

    return selected_options
