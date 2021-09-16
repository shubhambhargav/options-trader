from dataclasses import asdict
import json
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


def _enrich_options(options: List[models.OptionModel]) -> List[models.ProcessedOptionModel]:
    enriched_options = []
    margin_data = OptionsController.get_option_margin_bulk(options=options)

    # Following is used to avoid multiple calls to the underlying
    # instrument API
    instrument_data_cache = {}

    for iteration, option in enumerate(options):
        option = models.ProcessedOptionModel(**asdict(option))

        option.backup_money = option.strike * option.lot_size
        option.margin = margin_data[iteration]

        if option.underlying_instrument in instrument_data_cache:
            option.instrument_data = instrument_data_cache[option.underlying_instrument]
        else:
            option.instrument_data = InstrumentsController.get_instrument(tickersymbol=option.underlying_instrument)

            instrument_data_cache[option.underlying_instrument] = option.instrument_data


        profit = option.last_price * option.lot_size
        option.percentage_dip = (option.instrument_data.last_price - option.strike) / option.instrument_data.last_price * 100
        option.profit = models.OptionProfitModel(**{
            'value': profit,
            'percentage': (profit / option.margin.total) * 100
        })

        enriched_options.append(option)

    return enriched_options


def get_options_of_interest(stocks: List[models.StockOfInterest]) -> List[models.ProcessedOptionModel]:
    all_options = []

    for stock in stocks:
        stock = from_dict(data_class=models.StockOfInterest, data=stock)

        instrument = InstrumentsController.get_instrument(tickersymbol=stock.ticker)
        options = InstrumentsController.get_options_chain(instrument=instrument)

        options = list(filter(
            # Only interested in
            #   - PE options right now
            #   - valid PE i.e. less price than instrument_price
            #   - only looking for options within next X numeber of days
            lambda option: option.instrument_type == 'PE' \
                and option.strike < instrument.last_price \
                and option.time_to_expiry_in_days < VARIABLES.MAX_TIME_TO_EXPIRY \
                and stock.custom_filters.minimum_dip < ((instrument.last_price - option.strike) / instrument.last_price * 100) < stock.custom_filters.maximum_dip,
            options
        ))
        options = _enrich_options(options=options)

        all_options += options

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


def get_options_of_interest_df(stocks: List[models.StockOfInterest]) -> models.ProcessedOptionsModel:
    options_of_interest = get_options_of_interest(stocks=stocks)

    flattened_options_of_interest = Utilities.dict_array_to_df(
        dict_array=[asdict(option) for option in options_of_interest]
    )

    df = pd.DataFrame(flattened_options_of_interest)

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
