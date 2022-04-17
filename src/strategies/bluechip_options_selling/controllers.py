from collections import defaultdict
from datetime import date, timedelta
from importlib.resources import is_resource
from src.apps.kite.controllers.orders import OrdersController
from src.apps.kite.controllers.users import UsersController
from src.apps.kite.models.gtt import OrderModel
from src.apps.kite.models.instruments import CandleModel, EnrichedInstrumentModel
from src.apps.kite.models.positions import PositionModel
from src.apps.nse.models.options import HistoricalOptionModel
from typing import List

import emoji
from PyInquirer import Token, Separator, prompt, style_from_dict
from dacite import from_dict

from src.apps.telegram.controllers import TelegramController

from .models import BackTestConfigModel, ConfigModel
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
OPTIONS_MAX_TIME_TO_EXPIRY = 30  # in days
OPTIONS_EXIT_PROFIT_PERCENTAGE_THRESHOLD = 70  # in percentage


class BackTester:
    def __init__(self):
        self.config = None

    def get_stocks(self) -> List[StockOfInterest]:
        stocks_of_interest = [
            'COALINDIA', 'ICICIBANK', 'HDFCBANK', 'KOTAKBANK', 'BANDHANBNK',
            'HEROMOTOCO', 'TITAN', 'ASIANPAINT', 'MRF', 'HINDUNILVR',
            'MARUTI', 'NESTLEIND', 'INFY', 'TCS', 'HDFC', 'DRREDDY', 'TATACHEM',
            'RELIANCE', 'BHARTIARTL', 'PVR',
            'HDFCAMC', 'ITC', 'M&MFIN',
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

            if not options:
                LOGGER.debug('Processed for %s, no eligible options found' % stock.tickersymbol)

                continue

            options = OptionsController.enrich_options(options=options, on_date=on_date)

            all_options += options

            LOGGER.debug('Processed for %s' % stock.tickersymbol)

        return all_options

    def filter_instruments(self, instruments: List[EnrichedInstrumentModel]) -> List[EnrichedInstrumentModel]:
        filtered_instruments = []

        for instrument in instruments:
            # Skip the instruments which:
            #   - are already trading below last support because we don't know how low can they get
            #   - have already reached the last resistance i.e. no expected room to grow
            if instrument.close_last_by_resistance is None or instrument.close_last_by_support is None:
                LOGGER.info(
                    'Skipping instrument %s because insufficent data found: last support: %s, last resistance: %s' % (
                        instrument.tickersymbol, instrument.close_last_by_support, instrument.close_last_by_resistance
                    )
                )

                continue

            if instrument.close_last_by_support < 0 or instrument.close_last_by_resistance > 0:
                LOGGER.info(
                    'Skipping instrument %s because of -ve support or +ve resistance from close: %.2f last support and %.2f last resistance' % (
                        instrument.tickersymbol, instrument.close_last_by_support, instrument.close_last_by_resistance
                    )
                )

                continue

            support_resistance_gap = instrument.close_last_by_support + abs(instrument.close_last_by_resistance)

            percentage_up_from_support = instrument.close_last_by_support / support_resistance_gap * 100

            if percentage_up_from_support > self.config.entry_point_from_last_support:
                LOGGER.info(
                    'Skipping instrument %s because stock has already moved by %d percent from last support' % (
                        instrument.tickersymbol, percentage_up_from_support
                    )
                )

                continue

            filtered_instruments.append(instrument)

        return filtered_instruments

    def get_config(self):
        return from_dict(
            data_class=BackTestConfigModel,
            data={
                'available_margin': 1400000,  # 14 lakhs
                'entry_day_before_expiry_in_days': 25,
                'last_n_iterations': 7,
                'filter_stocks_by_technicals': True,
                'filter_options_by_open_int': True,
                'entry_point_from_last_support': 50,
                'filter_options_min_percentage_dip': 8,
                'filter_options_max_percentage_dip': 16,
                'filter_options_min_profit': 2000,
                'filter_options_max_profit': 15000,
                'filter_options_min_open_int': 0
            }
        )

    def run(self):
        stocks = self.get_stocks()
        self.config = self.get_config()

        print(self.config)

        entry_date = self.config.entry_day_before_expiry_in_days  # x days before the expiry
        last_n_iterations = self.config.last_n_iterations  # None depicts all
        filter_stocks_by_technicals = self.config.filter_stocks_by_technicals

        days_of_expiry = [
            date(2020, 1, 30), date(2020, 2, 27), date(2020, 3, 26), date(2020, 4, 30),
            date(2020, 5, 28), date(2020, 6, 25), date(2020, 7, 30), date(2020, 8, 27),
            date(2020, 9, 24), date(2020, 10, 29), date(2020, 11, 26), date(2020, 12, 31),
            date(2021, 1, 28), date(2021, 2, 25), date(2021, 3, 25), date(2021, 4, 29),
            date(2021, 5, 27), date(2021, 6, 24), date(2021, 7, 29), date(2021, 8, 26),
            date(2021, 9, 30)
        ]
        stock_market_holidays = [
            date(2020, 5, 25),  # not sure which holiday
            date(2021, 9, 10),  # Ganesh Chaturthi
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
            # Following is divided by 1.4 to accomodate for 40% margin needed on expiry
            # date. In-case the required margin exceeds available margin, it results into
            # incurring charges and interest on top of it.
            available_margin = self.config.available_margin / 1.4

            print('Processing for %s, expiry: %s' % (trade_day['on_date'], trade_day['expiry']))

            if filter_stocks_by_technicals:
                instruments: List[EnrichedInstrumentModel] = InstrumentsController.enrich_instruments(instruments=stocks, on_date=trade_day['on_date'])
                filtered_instruments = set([instrument.tickersymbol for instrument in  self.filter_instruments(instruments=instruments)])

                filtered_stocks = [stock for stock in stocks if stock.tickersymbol in filtered_instruments]

                LOGGER.info('Filtered %d stocks from %d' % (len(filtered_stocks), len(stocks)))
            else:
                filtered_stocks = stocks

            options = self._get_options(stocks=filtered_stocks, on_date=trade_day['on_date'])

            if self.config.filter_options_by_open_int:
                filter_function = lambda x: x.percentage_dip > self.config.filter_options_min_percentage_dip and x.percentage_dip < self.config.filter_options_max_percentage_dip \
                    and x.oi > self.config.filter_options_min_open_int \
                    and x.profit > self.config.filter_options_min_profit and x.profit < self.config.filter_options_max_profit
            else:
                filter_function = lambda x: x.percentage_dip > self.config.filter_options_min_percentage_dip and x.percentage_dip < self.config.filter_options_max_percentage_dip \
                    and x.profit > self.config.filter_options_min_profit and x.profit < self.config.filter_options_max_profit

            options = sorted(
                list(
                    filter(
                        filter_function,
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

                if available_margin < 50000:
                    # Margin < 50,000 INR doesn't get us anything, hence skipping
                    break

                selected_option: HistoricalOptionModel = list(option_list)[0]
                expected_pnl = selected_option.close * selected_option.lot_size

                instrument_expiry: CandleModel = InstrumentsController.get_instrument_price_details(
                    tickersymbol=selected_option.underlying_instrument,
                    on_date=trade_day['expiry']
                )

                available_margin -= selected_option.margin.total

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
    def __init__(self, config: ConfigModel = None, backtesting_enabled: bool = False):
        self.backtesting_enabled = backtesting_enabled
        self.config = config

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

    def _get_options(self) -> List[EnrichedOptionModel]:
        all_options = []

        for stock in self.config.stocks:
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

    def _manual_run(self):
        options = self._get_options()
        trade_options = self._get_options_of_interest(options=options)

        if self.config.is_order_enabled and options:
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

    def _filter_stocks(self) -> List[StockOfInterest]:
        instruments: List[EnrichedInstrumentModel] = InstrumentsController.enrich_instruments(instruments=self.config.stocks)

        filtered_instruments = []

        for instrument in instruments:
            # Skip the instruments which:
            #   - are already trading below last support because we don't know how low can they get
            #   - have already reached the last resistance i.e. no expected room to grow
            if instrument.close_last_by_resistance is None or instrument.close_last_by_support is None:
                LOGGER.info(
                    'Skipping instrument %s because insufficent data found: last support: %s, last resistance: %s' % (
                        instrument.tickersymbol, instrument.close_last_by_support, instrument.close_last_by_resistance
                    )
                )

                continue

            if instrument.close_last_by_support < 0 or instrument.close_last_by_resistance > 0:
                LOGGER.info(
                    'Skipping instrument %s because of -ve support or +ve resistance from close: %.2f last support and %.2f last resistance' % (
                        instrument.tickersymbol, instrument.close_last_by_support, instrument.close_last_by_resistance
                    )
                )

                continue

            support_resistance_gap = instrument.close_last_by_support + abs(instrument.close_last_by_resistance)

            percentage_up_from_support = instrument.close_last_by_support / support_resistance_gap * 100

            if percentage_up_from_support > self.config.automation_config.entry_point_from_last_support:
                LOGGER.info(
                    'Skipping instrument %s because stock has already moved by %d percent from last support' % (
                        instrument.tickersymbol, percentage_up_from_support
                    )
                )

                continue

            filtered_instruments.append(instrument)

        filtered_instruments = set([instrument.tickersymbol for instrument in  filtered_instruments])

        filtered_stocks = [stock for stock in self.config.stocks if stock.tickersymbol in filtered_instruments]

        return filtered_stocks

    def _filter_automated_options(self) -> List[EnrichedOptionModel]:
        options = self._get_options()

        if self.config.automation_config.filter_options_by_open_int:
            filter_function = lambda x: x.percentage_dip > self.config.automation_config.filter_options_min_percentage_dip and \
                    x.percentage_dip < self.config.automation_config.filter_options_max_percentage_dip \
                and x.oi > self.config.automation_config.filter_options_min_open_int \
                and x.profit > self.config.automation_config.filter_options_min_profit and x.profit < self.config.automation_config.filter_options_max_profit
        else:
            filter_function = lambda x: x.percentage_dip > self.config.automation_config.filter_options_min_percentage_dip and \
                    x.percentage_dip < self.config.automation_config.filter_options_max_percentage_dip \
                and x.profit > self.config.automation_config.filter_options_min_profit and x.profit < self.config.automation_config.filter_options_max_profit

        options = sorted(
            list(
                filter(
                    filter_function,
                    options
                )
            ),
            key=lambda x: x.profit, reverse=True
        )

        grouped_options = defaultdict(list)

        for option in options:
            grouped_options[option.underlying_instrument].append(option)

        return grouped_options

    def _automated_run(self, positions: List[PositionModel], orders: List[OrderModel]):
        # Workflow:
        #   - Filter stocks based on technicals
        #   - Filter options based on filtered stocks
        #   - Place an order based on the backtesting algorithm
        LOGGER.info('Config: %s' % self.config)

        # TODO: Make the following connected with 1.4 ratio of total available margin
        #       OR total available liquid margin
        min_margin_required = 200000  # 1 lakhs
        inital_stock_count = len(self.config.stocks)

        existing_instrument_options_positions = set()

        for elem in positions + orders:
            if not elem.tradingsymbol.endswith(('PE', 'CE')):
                continue

            instrument = Utilities.tradingsymbol_to_meta(tradingsymbol=elem.tradingsymbol)['instrument']

            existing_instrument_options_positions.add(instrument)

        today = date.today()

        if today.weekday() in [5, 6]:
            LOGGER.info('Not trading today as it is a weekend: %s' % today)

            return

        # if today.day > 10:
        #     LOGGER.info('Not trading after 10th day of the month, can we tweaked later...')

        #     return

        # Following is divided by 1.4 to accomodate for 40% margin needed on expiry
        # date. In-case the required margin exceeds available margin, it results into
        # incurring charges and interest on top of it.
        available_margin = UsersController.get_margins().equity.available.collateral / 1.4

        if available_margin < min_margin_required:
            LOGGER.info('Not trading due to margin ')

            return

        self.config.stocks = [stock for stock in self.config.stocks if stock.tickersymbol not in existing_instrument_options_positions]

        LOGGER.info('Short-listed %d stocks from %d based on previous orders/positions' % (len(self.config.stocks), inital_stock_count))

        self.config.stocks = self._filter_stocks() if self.config.automation_config.filter_stocks_by_technicals else self.config.stocks

        LOGGER.info('Short-listed %d stocks from %d based on technicals' % (len(self.config.stocks), inital_stock_count))
        LOGGER.info('Short-listed stocks: %s' % ', '.join([stock.tickersymbol for stock in self.config.stocks]))

        options = self._filter_automated_options()
        sold_options = []
        total_options_selected = 0

        for _, option_list in options.items():
            if not option_list:
                continue

            if available_margin < min_margin_required:
                # Margin < 50,000 INR doesn't get us anything, hence skipping
                LOGGER.info('Exhausted margin, remaining: %d' % available_margin)

                break

            selected_option: EnrichedOptionModel = list(option_list)[0]

            print(selected_option)

            total_options_selected += 1

            LOGGER.info('Selected option: %s, percent_dip: %.2f, profit: %d' % (selected_option.tradingsymbol, selected_option.percentage_dip, selected_option.profit))

            # is_sucess = OptionsController.sell_option(option=selected_option)
            is_sucess = True

            if is_sucess:
                sold_options.append(selected_option)

                available_margin = UsersController.get_margins().equity.available.collateral / 1.4

        if sold_options:
            telegram_message = 'Total options sold: %d out of selected: %d\n' % (len(sold_options), total_options_selected)

            telegram_message += '\n'.join([
                'Selected option: %s, percent_dip: %.2f, profit: %d' % (option.tradingsymbol, option.percentage_dip, option.profit) for option in sold_options
            ])

            TelegramController.send_message(message=telegram_message)

    def run(self):
        if not self.config:
            self.config = self.get_config()

        LOGGER.info('Total profit expected till now: %d' % PositionsController.get_pnl_month_end())

        # TODO: Filter out the active positions
        positions = PositionsController.get_positions()
        # TODO: Filter the active orders
        orders = OrdersController.get_orders(filter_is_open=True)

        if self.config.is_order_enabled:
            # TODO[Critical]: Capture the errors from cover nakes positions and send it to
            #       Telegram for debugging
            # Note for the following: Not using the futures anymore
            # PositionsController.cover_naked_positions()
            GTTController.remove_naked_gtts(positions=positions)

            if self.config.is_order_profit_booking_enabled:
                OptionsController.exit_profited_options(profit_percentage_threshold=OPTIONS_EXIT_PROFIT_PERCENTAGE_THRESHOLD)

        if not self.config.is_automated:
            self._manual_run()
        else:
            self._automated_run(positions=positions, orders=orders)
