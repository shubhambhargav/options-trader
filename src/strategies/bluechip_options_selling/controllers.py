from collections import defaultdict
from datetime import date, timedelta
from src.apps.kite.models.instruments import CandleModel
from src.apps.nse.models.options import HistoricalOptionModel
from typing import List

import emoji
from PyInquirer import Token, Separator, prompt, style_from_dict
from dacite import from_dict

from .models import ConfigModel
import src.utilities as Utilities
from src.apps.kite.models import StockOfInterest, EnrichedOptionModel
from src.apps.kite.controllers import (
    InstrumentsController, OptionsController, PositionsController, GTTController
)
from src.apps.nse.controllers.options import OptionsController as NSEOptionsController
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


class BackTester:
    def __init__(self):
        pass

    def get_stocks(self) -> List[StockOfInterest]:
        stocks_of_interest = [
            'COALINDIA', 'ICICIBANK', 'HDFCBANK', 'KOTAKBANK', # 'BANDHANBNK',
            'HEROMOTOCO', 'TITAN', 'ASIANPAINT', 'MRF', 'HINDUNILVR',
            'MARUTI', 'NESTLEIND', 'INFY', 'TCS', 'HDFC', 'DRREDDY', 'TATACHEM',
            'RELIANCE', 'BHARTIARTL', # 'PVR'
        ]

        stocks = [{ 'tickersymbol': stock } for stock in stocks_of_interest]

        return [from_dict(data_class=StockOfInterest, data=stock) for stock in stocks]

    def _get_options(self, stocks: List[StockOfInterest], on_date: date) -> List[HistoricalOptionModel]:
        all_options = []

        for stock in stocks:
            instrument = InstrumentsController.get_instrument(tickersymbol=stock.tickersymbol, on_date=on_date)
            options = InstrumentsController.get_options_chain(instrument=instrument, on_date=on_date)

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
            options = OptionsController.enrich_options(options=options, on_date=on_date)

            all_options += options

            LOGGER.debug('Processed for %s' % stock.tickersymbol)

        return all_options

    def run(self):
        stocks = self.get_stocks()

        entry_date = 20  # x days before the expiry
        last_n_iterations = 3  # None depicts all

        days_of_expiry = [
            date(2020, 1, 30), date(2020, 2, 27), date(2020, 3, 26), date(2020, 4, 30),
            date(2020, 5, 28), date(2020, 6, 25), date(2020, 7, 30), date(2020, 8, 27),
            date(2020, 9, 24), date(2020, 10, 29), date(2020, 11, 26), date(2020, 12, 31),
            date(2021, 1, 28), date(2021, 2, 25), date(2021, 3, 25), date(2021, 4, 29),
            date(2021, 5, 27), date(2021, 6, 24), date(2021, 7, 29), date(2021, 8, 26),
            date(2021, 9, 30)
        ]
        stock_market_holidays = [
            date(2021, 9, 10)  # Ganesh Chaturthi
        ]

        days_of_trading = []

        for expiry in days_of_expiry:
            trading_day = expiry - timedelta(days=entry_date)

            if trading_day.weekday() not in [0, 1, 2, 3, 4]:
                trading_day += timedelta(days=7 - trading_day.weekday())

            if trading_day in stock_market_holidays:
                trading_day += timedelta(days=1 if trading_day.weekday() in [0, 1, 2, 3] else 3)

            days_of_trading.append({
                'on_date': trading_day,
                'expiry': expiry
            })

        if last_n_iterations:
            days_of_trading = days_of_trading[-1 * last_n_iterations:]

        # TODO
        # 1. Add the custom entry point
        # 2. Add the day based actions (optional)
        # 2.1 Figure out if the GTT will even trigger

        total_pnl = 0
        total_optimistic_pnl = 0
        total_expected_pnl = 0
        positions = defaultdict(list)

        for trade_day in days_of_trading:
            print('Processing for %s, expiry: %s' % (trade_day['on_date'], trade_day['expiry']))

            options = self._get_options(stocks=stocks, on_date=trade_day['on_date'])

            options = sorted(
                list(
                    filter(
                        lambda x: x.percentage_dip > 10 and x.percentage_dip < 16 \
                            and x.open_int > 0 \
                            and x.profit > 2000 and x.profit < 15000,
                        options
                    )
                ),
                key=lambda x: x.profit, reverse=True
            )

            grouped_options = defaultdict(list)

            for option in options:
                grouped_options[option.underlying_instrument].append(option)

            for _, option_list in grouped_options.items():
                if not option_list:
                    continue

                selected_option: HistoricalOptionModel = list(option_list)[0]
                expected_pnl = selected_option.close * selected_option.lot_size

                instrument_expiry: CandleModel = InstrumentsController.get_instrument_price_details(
                    tickersymbol=selected_option.underlying_instrument,
                    on_date=trade_day['expiry']
                )

                if instrument_expiry.close >= selected_option.strike:
                    pnl = expected_pnl
                    expiry_data = None
                else:
                    expiry_data = NSEOptionsController.get_historical_data(
                        tickersymbol=selected_option.underlying_instrument,
                        expiry_date=trade_day['expiry'],
                        option_types=[selected_option.instrument_type],
                        strike_price=selected_option.strike,
                        from_date=trade_day['expiry'],
                        to_date=trade_day['expiry']
                    )

                    if not expiry_data:
                        print('Could not find the expiry data for option: ', selected_option)

                        continue

                    expiry_data = expiry_data[0]

                    pnl = (selected_option.last_price - expiry_data.close) * selected_option.lot_size

                optimistic_pnl = 0 if pnl < 0 else pnl

                positions[trade_day['on_date']].append({
                    'position': selected_option,
                    'expiry': expiry_data,
                    'expected_pnl': expected_pnl,
                    'optimistic_pnl': optimistic_pnl,
                    'pnl': pnl
                })

                total_expected_pnl += expected_pnl
                total_pnl += pnl
                total_optimistic_pnl += optimistic_pnl

            print('Positions taken on %s' % trade_day['on_date'])
            print('\n'.join([
                'symbol: %s strike: %s dip: %.2f expected-pnl: %.2f real-pnl: %.2f, margin: %.2f\topen_int: %.2f' % (
                    position['position'].symbol, position['position'].strike, position['position'].percentage_dip,
                    position['expected_pnl'], position['pnl'], position['position'].margin.total,
                    position['position'].open_int
                ) \
                    for position in positions[trade_day['on_date']]
            ]))
            print(
                'Real-Pnl: %.2f, Optimistic-Pnl: %.2f, Expected-Pnl: %.2f, Margin: %.2f' % (
                    sum(position['pnl'] for position in positions[trade_day['on_date']]),
                    sum(position['optimistic_pnl'] for position in positions[trade_day['on_date']]),
                    sum(position['expected_pnl'] for position in positions[trade_day['on_date']]),
                    sum(position['position'].margin.total for position in positions[trade_day['on_date']])
                )
            )

        print('\nReal-pnl: %.2f, Optimistic-pnl: %.2f, Total expected-pnl: %.2f ' % (total_pnl, total_optimistic_pnl, total_expected_pnl))


class BluechipOptionsSeller:
    def __init__(self, backtesting_enabled: bool = False):
        self.backtesting_enabled = backtesting_enabled

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
                    Separator('= Tech ='),
                    { 'name': 'INFY' },
                    { 'name': 'TCS' },
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
            { 'name': 'close_by_min', 'from': 'enriched_instrument.close_last_by_min', 'print_size': 12, 'format': '%.2f' },
            { 'name': 'close_by_avg', 'from': 'enriched_instrument.close_last_by_avg', 'print_size': 12, 'format': '%.2f' },
            { 'name': 'close_by_support', 'from': 'enriched_instrument.close_last_by_support', 'print_size': 12, 'format': '%.2f' },
            { 'name': 'close_by_resist', 'from': 'enriched_instrument.close_last_by_resistance', 'print_size': 12, 'format': '%.2f' },
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
