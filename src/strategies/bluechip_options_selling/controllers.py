from typing import List

import emoji
import pandas as pd
from PyInquirer import Token, Separator, prompt, style_from_dict
from dacite import from_dict

from .models import ConfigModel
import src.utilities as Utilities
from src.apps.kite.models import StockOfInterest, EnrichedOptionModel
from src.apps.kite.controllers import (
    InstrumentsController, OptionsController, PositionsController, GTTController
)
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
                    { 'name': 'ICICIBANK' },
                    { 'name': 'IDFCFIRSTB' },
                    { 'name': 'HDFCBANK' },
                    { 'name': 'M&MFIN' },
                    { 'name': 'KOTAKBANK' },
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
                    { 'name': 'HDFC' },
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

    def _get_options(self, stocks: List[StockOfInterest]) -> List[EnrichedOptionModel]:
        all_options = []

        for stock in stocks:
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

        return all_options

    def _get_options_of_interest(self, options: List[EnrichedOptionModel]):
        options = sorted(options, key=lambda option: option.underlying_instrument + option.expiry)

        parsed_options = []
        default_print_size = 10
        columns = [
            # Following needs to be sequence for printing
            { 'name': 'instrument', 'from': 'underlying_instrument', 'primary_key': True, 'print_size': 16 },
            { 'name': 'expiry', 'secondary_key': True, 'print_size': 16 },
            { 'name': 'instru_price', 'from': 'instrument_data.close_price', 'print_size': 14 },
            { 'name': 'close_last_by_min', 'from': 'enriched_instrument.close_last_by_min', 'print_size': 18, 'format': '%.2f' },
            { 'name': 'close_last_by_avg', 'from': 'enriched_instrument.close_last_by_avg', 'print_size': 18, 'format': '%.2f' },
            { 'name': 'last_buy_signal', 'from': 'enriched_instrument.last_buy_signal', 'print_size': 14  },
            { 'name': 'existing', 'print_size': 10 },
            { 'name': '%_dip', 'from': 'percentage_dip', 'print_size': 8, 'format': '%.2f' },
            { 'name': 'profit', 'print_size': 12, 'format': '%.2f' },
            { 'name': '%_profit', 'from': 'profit_percentage', 'format': '%.2f' },
            { 'name': 'strike', 'print_size': 8, 'format': '%.2f' },
            { 'name': 'last_price', 'format': '%.2f' },
            { 'name': 'margin', 'from': 'margin.total', 'print_size': 14, 'format': '%.2f' },
            { 'name': 'backup_money', 'print_size': 16, 'format': '%.2f' }
        ]
        prev_option_key = None
        prev_option_instrument = None
        print_format = ' '.join(['{:<%s}' % col.get('print_size', default_print_size) for col in columns])
        key_columns = [col['name'] for col in columns if col.get('primary_key') or col.get('secondary_key')]
        non_key_columns = [col['name'] for col in columns if not (col.get('primary_key') or col.get('secondary_key'))]
        primary_key_columns = [col['name'] for col in columns if col.get('primary_key')]
        secondary_key_columns = [col['name'] for col in columns if col.get('secondary_key')]

        for option in options:
            option_dict = {}
            option_dict['object'] = option

            for col in columns:
                obj_attribute = col['from'] if col.get('from') else col['name']

                option_dict[col['name']] = Utilities.deepgetattr(option, obj_attribute)

                if col.get('format'):
                    option_dict[col['name']] = col['format'] % option_dict[col['name']]

            option_dict['existing'] = 'NA'

            if option.instrument_positions:
                option_dict['instrument'] = emoji.emojize(
                    option_dict['instrument'] + ' :white_check_mark:',
                    use_aliases=True
                )

            if option.orders:
                option_dict['existing'] = emoji.emojize(':package:')

            if option.position:
                option_dict['existing'] = emoji.emojize(
                    str(abs(option.position.quantity)) + ' :white_check_mark:',
                    use_aliases=True
                )

            current_option_key = '|'.join([option_dict[col] for col in key_columns])

            if current_option_key == prev_option_key:
                option_dict['__str__'] = print_format.format(*(
                    ['' for _ in range(len(key_columns))] +
                        [str(option_dict[col]) for col in non_key_columns]
                ))
            elif option_dict['instrument'] == prev_option_instrument:
                option_dict['__str__'] = print_format.format(*(
                    ['' for _ in range(len(primary_key_columns))] +
                        [str(option_dict[col]) for col in (secondary_key_columns + non_key_columns)]
                ))
            else:
                option_dict['__str__'] = print_format.format(*[str(option_dict[col]) for col in (key_columns + non_key_columns)])

            prev_option_key = current_option_key
            prev_option_instrument = option_dict['instrument']

            parsed_options.append(option_dict)

        questions = [
            {
                'type': 'checkbox',
                'name': 'options',
                'message': 'List of options to be bought!',
                'choices': [
                    Separator('  ' + print_format.format(*([col['name'] for col in columns])))
                ] + [
                    {
                        'name': option['__str__'],
                        'value': option['object']
                    } for option in parsed_options
                ]
            }
        ]

        response = prompt(questions=questions, style=STYLE)

        return response.get('options', [])

    def _trade_options(self, options: List[EnrichedOptionModel]):
        expected_profit = 0
        margin_required = 0

        expected_profit = sum([option.profit for option in options])
        margin_required = sum([option.margin.total for option in options])

        LOGGER.info('Expected profit: %d, margin: %d' % (expected_profit, margin_required))

        for option in options:
            OptionsController.sell_option(option=option)

    def run(self):
        config = self.get_config()

        LOGGER.info('Total profit expected till now: %d' % PositionsController.get_pnl_month_end())

        if config.is_order_enabled:
            PositionsController.cover_naked_positions()
            GTTController.remove_naked_gtts(positions=PositionsController.get_positions())

            if config.is_order_profit_booking_enabled:
                OptionsController.exit_profited_options(profit_percentage_threshold=OPTIONS_EXIT_PROFIT_PERCENTAGE_THRESHOLD)

        options = self._get_options(stocks=config.stocks)
        trade_options = self._get_options_of_interest(options=options)

        if config.is_order_enabled and options:
            self._trade_options(options=trade_options)

            to_continue_question = [{
                'type': 'confirm',
                'name': 'continue',
                'message': 'Would you like to trade more from the existing options?',
                'default': False
            }]

            to_continue = prompt(questions=to_continue_question, style=STYLE)['continue']

            while to_continue:
                options = OptionsController.update_orders(options=options)
                trade_options = self._get_options_of_interest(options=options)

                self._trade_options(options=trade_options)

                to_continue = prompt(questions=to_continue_question, style=STYLE)['continue']
