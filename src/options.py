from dataclasses import asdict
from numpy import isnan
from src.controllers.options import OptionsController
from src.models.instruments import InstrumentModel
import pandas as pd
from typing import List

from dacite import from_dict

try:
    from ._variables import VARIABLES
    from . import utilities as Utilities
    from . import models
    from .controllers.instruments import InstrumentsController
except:
    # In order to run the module in isolation, following is required
    # This enables local testing
    from _variables import VARIABLES
    import utilities as Utilities


def get_options_of_interest(stocks: List[models.StockOfInterest]) -> List[models.EnrichedOptionModel]:
    all_options = []

    for stock in stocks:
        stock = from_dict(data_class=models.StockOfInterest, data=stock)

        instrument = InstrumentsController.get_instrument(tickersymbol=stock.tickersymbol)
        options = InstrumentsController.get_options_chain(instrument=instrument)

        options = list(filter(
            # Only interested in
            #   - PE options
            #   - valid PE i.e. less price than instrument_price
            #   - only looking for options within next X numeber of days
            lambda option: option.instrument_type == 'PE' \
                and option.strike < instrument.last_price \
                and option.time_to_expiry_in_days < VARIABLES.MAX_TIME_TO_EXPIRY \
                and stock.custom_filters.minimum_dip < ((instrument.last_price - option.strike) / instrument.last_price * 100) < stock.custom_filters.maximum_dip,
            options
        ))
        options = OptionsController.enrich_options(options=options)

        all_options += options

        print('Processed for %s' % stock.tickersymbol)

    all_options = list(filter(
        lambda elem: elem.profit__percentage >= VARIABLES.MINIMUM_PROFIT_PERCENTAGE,
        sorted(
            all_options, key=lambda x: x.profit__percentage + x.percentage_dip, reverse=True
        )
    ))

    for seq_no in range(len(all_options)):
        all_options[seq_no].sequence_id = seq_no + 1

    return all_options


def get_options_of_interest_df(stocks: List[models.StockOfInterest]) -> models.EnrichedOptionModel:
    options_of_interest = get_options_of_interest(stocks=stocks)

    flattened_options_of_interest = Utilities.dict_array_to_df(
        dict_array=[asdict(option) for option in options_of_interest]
    )

    df = pd.json_normalize(flattened_options_of_interest)

    if len(df) == 0:
        return df

    return df


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
