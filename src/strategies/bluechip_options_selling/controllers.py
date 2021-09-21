from dataclasses import asdict
from typing import List

import emoji
from numpy import isnan
import pandas as pd
from PyInquirer import Token, Separator, prompt, style_from_dict
from dacite import from_dict

from .models import ConfigModel
import src.utilities as Utilities
from src.apps.kite.models import StockOfInterest, EnrichedOptionModel
from src.apps.kite.controllers import InstrumentsController, OptionsController, PositionsController
from src.logger import LOGGER

STYLE = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})
OPTIONS_MINIMUM_PROFIT_PERCENTAGE = 2  # in percentage
OPTIONS_MAX_TIME_TO_EXPIRY = 40  # in days
OPTIONS_EXIT_PROFIT_PERCENTAGE_THRESHOLD = 90  # in percentage


class BluechipOptionsSeller:
    def __init__(self):
        pass

    def get_config(self) -> ConfigModel:
        questions = [
            {
                'type': 'confirm',
                'name': 'is_order_enabled',
                'message': 'Enable automated ordering?',
                'default': True
            },
            {
                'type': 'confirm',
                'name': 'is_order_profit_booking_enabled',
                'message': 'Close profited (90%+ profit) option positions?',
                'default': False
            },
            {
                'type': 'checkbox',
                'name': 'stocks',
                'message': 'List of stocks to be processed!',
                'choices': [
                    Separator('= Public Sector ='),
                    { 'name': 'COALINDIA' },
                    Separator('= Banking & Finance ='),
                    { 'name': 'HDFC', 'checked': True },
                    { 'name': 'ICICIBANK' },
                    { 'name': 'IDFCFIRSTB' },
                    { 'name': 'HDFCBANK' },
                    { 'name': 'M&MFIN' },
                    { 'name': 'KOTAKBANK'},
                    { 'name': 'BANDHANBNK' },
                    Separator('= Insurance ='),
                    { 'name': 'HDFCLIFE' },
                    Separator('= FMCG ='),
                    { 'name': 'HEROMOTOCO' },
                    { 'name': 'TITAN' },
                    { 'name': 'PIDILITIND' },
                    { 'name': 'ASIANPAINT' },
                    { 'name': 'MRF' },
                    { 'name': 'HINDUNILVR' },
                    { 'name': 'MARUTI' },
                    { 'name': 'NESTLEIND' },
                    Separator('= Emerging Market ='),
                    { 'name': 'HDFCAMC' },
                    Separator('= Tech ='),
                    { 'name': 'INFY' },
                    { 'name': 'TCS' },
                    { 'name': 'NAUKRI' },
                    { 'name': 'COFORGE' },
                    { 'name': 'MINDTREE' },
                    { 'name': 'LTI' },
                    { 'name': 'HCLTECH' },
                    Separator('= Uncategorized ='),
                    { 'name': 'DRREDDY' },
                    { 'name': 'TATACHEM' },
                    { 'name': 'RELIANCE' },
                    { 'name': 'BHARTIARTL' },
                    { 'name': 'PVR' },
                    { 'name': 'ITC' },
                ]
            }
        ]

        config = prompt(questions=questions, style=STYLE)
        config['stocks'] = [{ 'tickersymbol': stock } for stock in config['stocks']]

        return from_dict(data_class=ConfigModel, data=config)

    def _get_options_of_interest(self, stocks: List[StockOfInterest]) -> List[EnrichedOptionModel]:
        all_options = []

        for stock in stocks:
            stock = from_dict(data_class=StockOfInterest, data=stock)

            instrument = InstrumentsController.get_instrument(tickersymbol=stock.tickersymbol)
            options = InstrumentsController.get_options_chain(instrument=instrument)

            options = list(filter(
                # Only interested in
                #   - PE options
                #   - valid PE i.e. less price than instrument_price
                #   - only looking for options within next X numeber of days
                lambda option: option.instrument_type == 'PE' \
                    and option.strike < instrument.last_price \
                    and option.time_to_expiry_in_days < OPTIONS_MAX_TIME_TO_EXPIRY \
                    and stock.custom_filters.minimum_dip < ((instrument.last_price - option.strike) / instrument.last_price * 100) < stock.custom_filters.maximum_dip,
                options
            ))
            options = OptionsController.enrich_options(options=options)

            all_options += options

            LOGGER.debug('Processed for %s' % stock.tickersymbol)

        all_options = list(filter(
            lambda elem: elem.profit_percentage >= OPTIONS_MINIMUM_PROFIT_PERCENTAGE,
            sorted(
                all_options, key=lambda x: x.profit_percentage + x.percentage_dip, reverse=True
            )
        ))

        for seq_no in range(len(all_options)):
            all_options[seq_no].sequence_id = seq_no + 1

        return all_options

    def _print_options_of_interest(self, options_df: pd.DataFrame):
        # Following has been copied to place orders while the original df can be altered
        # TODO | WARN: Avoid doing this since this could result into wrong order placement
        copied_options_df = options_df.copy(deep=True)

        # Add metadata about current positions
        copied_options_df.underlying_instrument[copied_options_df.instrument_positions.notnull()] = copied_options_df.underlying_instrument.apply(
            lambda x: emoji.emojize(x + ' :white_check_mark:', use_aliases=True)
        )
        options_df['existing'] = 'NA'

        if 'position__quantity' in list(copied_options_df.columns):
            copied_options_df['existing'] = (copied_options_df.position__quantity / copied_options_df.lot_size).apply(
                lambda x: 'NA' if isnan(x) else emoji.emojize(str(abs(x)) + ' :white_check_mark:', use_aliases=True)
            )

        copied_options_df.rename(
            columns={
                'sequence_id': 'seq',
                'underlying_instrument': 'instrument',
                'instrument_data__close_price': 'instrument_price',
                'percentage_dip': '%_dip',
                'profit_percentage': '%_profit',
                'margin__total': 'margin',
                'enriched_instrument__close_last_by_min': 'close_last_by_min',
                'enriched_instrument__close_last_by_avg': 'close_last_by_avg',
                'enriched_instrument__last_buy_signal': 'last_buy_signal'
            },
            inplace=True
        )

        indexed_options = copied_options_df \
            .sort_values(['instrument', 'expiry']) \
            .set_index(['instrument', 'instrument_price', 'expiry', 'close_last_by_min', 'close_last_by_avg', 'last_buy_signal'])

        columns = [
            'seq', 'recommendation', 'existing', '%_dip', 'profit', '%_profit', 'strike', 'last_price', 'margin', 'backup_money'
        ]

        print(indexed_options[columns].to_string())

    def _trade_options(self, options_df: pd.DataFrame):
        seq_ids = input('Select the options to trade: ')
        seq_ids = seq_ids.split(',')
        options = [Utilities.unflatten_dict(data=option) for option in options_df.T.to_dict().values()]

        option_dict = dict((option['sequence_id'], option) for option in options)
        selected_options = []
        expected_info = {
            'profit': 0,
            'margin': 0
        }

        for seq_id in seq_ids:
            option = option_dict[int(seq_id)]

            selected_options.append(option)

            expected_info['profit'] += option['profit']
            expected_info['margin'] += option['margin']['total']

        LOGGER.info('Expected profit: %d, margin: %d' % (expected_info['profit'], expected_info['margin__total']))

        for option in selected_options:
            OptionsController.sell_option(option=option)

    def run(self):
        config = self.get_config()

        if config.is_order_enabled:
            PositionsController.cover_naked_positions()

            if config.is_order_profit_booking_enabled:
                OptionsController.exit_profited_options(profit_percentage_threshold=OPTIONS_EXIT_PROFIT_PERCENTAGE_THRESHOLD)

        options = self._get_options_of_interest(stocks=config.stocks)
        options = [Utilities.flatten_dict(data=asdict(option)) for option in options]

        options_df = pd.json_normalize(options)
        options_df.sequence_id = options_df.sequence_id.fillna(-100).astype(int)

        self._print_options_of_interest(options_df=options_df)

        if config.is_order_enabled:
            self._trade_options(options_df=options_df)




