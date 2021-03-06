from copy import deepcopy
import re
from datetime import date, datetime, timedelta
from typing import List
from urllib.parse import quote_plus

import numpy
from PyInquirer import Token, prompt, style_from_dict
from dacite.core import from_dict

from src.apps.kite.controllers.positions import PositionsController
from src.apps.kite.controllers.instruments import InstrumentsController
from src.apps.kite.controllers.options import OptionsController
from src.apps.kite.controllers.users import UsersController
from src.apps.kite.models.positions import PositionModel
from src.apps.nse.models.options import HistoricalOptionModel
from src.apps.settings.controllers.config import ConfigController
from src.strategies.strangling.models import ConfigModel, ConfigV2Model, MockPositionModel
from src.logger import LOGGER
from src import utilities as Utilities

STYLE = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})
OPTIONS_TICKERSYMBOL_DATETIME_FORMAT = '%y%b%d'
STOCK_OPTIONS_TICKERSYMBOL_DATETIME_FORMAT = '%d%b'

POSITIONS_DICT = {}
GLOBAL_CONFIG: ConfigV2Model = None
DONE_CODE = 1000


def _get_weekly_option_tickersymbol(instrument: str, option_type: str, expiry: date, price: float):
    return '%(instrument)s%(expiry_year)s%(expiry_month)s%(expiry_day)s%(price)s%(option_type)s' % {
        'instrument': instrument,
        'expiry_year': expiry.strftime('%y'),
        'expiry_month': expiry.strftime('%b').upper()[0],
        'expiry_day': expiry.strftime('%d'),
        'price': price,
        'option_type': option_type
    }


def process_ticks(ticks: list) -> bool:
    global GLOBAL_CONFIG
    global POSITIONS_DICT

    now = datetime.now()

    # Exit the strategy to book the pnl for the day
    if now.hour > 15 and now.minute > 15:
        total_pnl = sum([position.pnl for position in POSITIONS_DICT.values()])

        LOGGER.info('Booking the profit for the day: %.2f' % total_pnl)

        if not GLOBAL_CONFIG.is_mock_run:
            for position in POSITIONS_DICT.values():
                PositionsController.exit_position(position=position)

        return True

    for tick in ticks:
        LOGGER.info(tick)

        position: PositionModel = POSITIONS_DICT[str(tick['instrument_token'])]

        if position.tradingsymbol.endswith('PE'):
            position.pnl = (position.average_price - tick['last_price']) *  abs(position.quantity)
        elif position.tradingsymbol.endswith('CE'):
            position.pnl = (tick['last_price'] - position.average_price) * abs(position.quantity)
        else:
            raise ValueError('Unexpected tickersymbol found: %s' % position.tradingsymbol)

    total_pnl = sum([position.pnl for position in POSITIONS_DICT.values()])

    if total_pnl < GLOBAL_CONFIG.stoploss_pnl:
        LOGGER.info(
            'Exiting the positions; condition met; stoploss_pnl: %d, current pnl: %.2f' % (
                GLOBAL_CONFIG.stoploss_pnl, total_pnl
            )
        )

        if not GLOBAL_CONFIG.is_mock_run:
            for position in POSITIONS_DICT.values():
                PositionsController.exit_position(position=position)

        return True

def on_ticks(ws, ticks):
    try:
        is_breaking_required = process_ticks(ticks=ticks)
    except Exception as ex:
        LOGGER.error(ex)

        ws.close(code=DONE_CODE)

        return

    if is_breaking_required:
        ws.close(code=DONE_CODE)


def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    global POSITIONS_DICT

    position_tokens = [position.instrument_token for position in POSITIONS_DICT.values()]

    ws.subscribe(position_tokens)

    # Set all instruments to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, position_tokens)


def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    if code == DONE_CODE:
        # Closing the connection once the stoploss is met
        ws.stop()


class Strangler:
    def __init__(self, config: ConfigV2Model = None):
        self.config = config

    def _enter_market(self, option_gap: int, on_date: date = None):
        global POSITIONS

        tickersymbol = self.config.tickersymbol
        strangle_gap = self.config.strangle_gap

        today = datetime.today() if not on_date else on_date

        # TODO: Verify if the following works correctly
        if on_date:
            instrument_price = InstrumentsController.get_instrument_price_details(tickersymbol=tickersymbol, on_date=on_date).open
        else:
            instrument_price = InstrumentsController.get_last_trading_price(tickersymbol=tickersymbol)

        instrument_token_dict = InstrumentsController.get_instrument_token_dict()

        low_sell_price = Utilities.round_nearest(number=instrument_price - strangle_gap, unit=option_gap, direction='down')
        high_sell_price = Utilities.round_nearest(number=instrument_price + strangle_gap, unit=option_gap, direction='up')

        instrument = InstrumentsController.get_instrument(tickersymbol=tickersymbol, on_date=on_date)
        options = InstrumentsController.get_options_chain(instrument=instrument, on_date=on_date)

        if on_date:
            options_dict = {}

            for option in options:
                symbol = '%s%s%s%s' % (
                    option.tradingsymbol, ''.join(option.expiry.split('-')[:2]).upper(),
                    int(option.strike_price) if option.strike_price.is_integer() else option.strike_price,
                    option.instrument_type
                )

                option.tradingsymbol = symbol

                setattr(option, 'instrument_token', 0)

                options_dict[symbol] = option
        else:
            options_dict = dict((option.tradingsymbol, option) for option in options)

        next_thursday = Utilities.get_next_closest_thursday(dt=today)

        high_option = options_dict[_get_weekly_option_tickersymbol(instrument=tickersymbol, option_type='CE', expiry=next_thursday, price=high_sell_price)]
        low_option = options_dict[_get_weekly_option_tickersymbol(instrument=tickersymbol, option_type='PE', expiry=next_thursday, price=low_sell_price)]

        high_option.lot_size = self.config.number_of_lots * high_option.lot_size
        low_option.lot_size = self.config.number_of_lots * low_option.lot_size

        if self.config.is_mock_run:
            POSITIONS_DICT.update({
                instrument_token_dict[high_option.tradingsymbol]: from_dict(
                    data_class=MockPositionModel,
                    data={
                        'tradingsymbol': high_option.tradingsymbol,
                        'average_price': high_option.last_price,
                        'instrument_token': high_option.instrument_token,
                        'quantity': high_option.lot_size,
                        'pnl': 0.0
                    }
                ),
                instrument_token_dict[low_option.tradingsymbol]: from_dict(
                    data_class=MockPositionModel,
                    data={
                        'tradingsymbol': low_option.tradingsymbol,
                        'average_price': low_option.last_price,
                        'instrument_token': low_option.instrument_token,
                        'quantity': low_option.lot_size,
                        'pnl': 0.0
                    }
                )
            })

            LOGGER.info('Sold upper option: %s' % high_option)
            LOGGER.info('Sold lower option: %s' % low_option)

            if self.config.is_backtest:
                return [high_option, low_option]

            return POSITIONS_DICT

        OptionsController.sell_option(option=high_option)
        OptionsController.sell_option(option=low_option)

        LOGGER.info('Sold upper option: %s' % high_option)
        LOGGER.info('Sold lower option: %s' % low_option)

        positions = PositionsController.get_positions()

        for position in positions:
            if position.tradingsymbol in [high_option.tradingsymbol, low_option.tradingsymbol]:
                POSITIONS_DICT[instrument_token_dict[position.tradingsymbol]] = position

        return POSITIONS_DICT

    def get_config(self):
        questions = [
            {
                'type': 'list',
                'name': 'tickersymbol',
                'message': 'List of stocks to be processed!',
                'choices': [
                    { 'name': 'NIFTY' }
                ],
                'default': 0
            },
            {
                'type': 'input',
                'name': 'strangle_gap',
                'message': 'Gap of strangle in indice points',
                'default': '200'
            },
            {
                'type': 'input',
                'name': 'stoploss_pnl',
                'message': 'Stoploss PnL (negative value for loss)',
                'default': '-1000'
            },
            {
                'type': 'confirm',
                'name': 'is_mock_run',
                'message': 'Would you like to run the program as mock?',
                'default': False
            }
        ]

        config = prompt(questions=questions, style=STYLE)

        config['strangle_gap'] = int(config['strangle_gap'])
        config['stoploss_pnl'] = int(config['stoploss_pnl'])

        return from_dict(data_class=ConfigV2Model, data=config)

    def run(self):
        # In order to keep the requirements clean for deployments, the underlying twisted module is
        # considered for development purposes only as of now, hence the following import is localized
        from src.apps.kite.connectors.websocket import KiteTicker

        if not self.config:
            self.config = self.get_config()

        global GLOBAL_CONFIG

        GLOBAL_CONFIG = self.config

        # Following code has hard-coded values as of now
        # TODO (overall):
        #       - (Done) Add auto-login for TOTP
        #       - (Done) Add market entry logic
        #       - (Done) Add configuration for stoploss and mock runs
        #       - (Done) Add realtime subscription for instruments
        #       - (Done) Add stoploss execution
        #       - (Done) Add exit strategy given the timestamp
        #       - (Done) Testing ------
        #       - (Done) Add logging for sample run
        #       - [Optional] Add backtesting -- will help with testing
        #       - Testing ------
        #       - (Done) Add CLI setup for automation triggering
        #       - (Done; sort-of) [Advanced] Add program termination after market closure to save PC resources
        #       - (Done; with assumptions)[Advanced] Account for cookie conflict with browser login
        #       - [Advanced] Solve the bug where current expiry day is not account for on Thursdays
        # Assumptions to be verified:
        #       - Last price API works
        #       - Connection termination in-between doesn't break the execution
        #       - The end of the day execution happens for closure
        nifty_option_gap = 50
        now = datetime.now()

        if self.config.tickersymbol != 'NIFTY':
            raise NotImplementedError('The program has only bee implemented for NIFTY as of now.')

        if now.weekday() not in [0, 1, 2, 3, 4]:
            LOGGER.info('Found weekend, not trading...')

            return

        # TODO: Add the ability to resume the operations from already existing positions
        self._enter_market(option_gap=nifty_option_gap)

        kws = KiteTicker(
            user_id=UsersController.get_current_user().user_id,
            enctoken=quote_plus(ConfigController.get_config().kite_auth_token)
        )

        # Assign the callbacks.
        kws.on_ticks = on_ticks
        kws.on_connect = on_connect
        kws.on_close = on_close

        # Infinite loop on the main thread. Nothing after this will run.
        # You have to use the pre-defined callbacks to manage subscriptions.
        kws.connect()

    def get_backtest_config(self) -> ConfigV2Model:
        config = {
            'tickersymbol': 'NIFTY',
            'strangle_gap': 200,
            'stoploss_pnl': -1000,
            'is_mock_run': True,
            'is_backtest': True
        }

        return from_dict(data_class=ConfigV2Model, data=config)

    def backtest(self, from_date: date, to_date: date):
        global POSITIONS_DICT

        self.config = self.get_backtest_config()
        nifty_option_gap = 50

        if self.config.tickersymbol != 'NIFTY':
            raise NotImplementedError('The program has only bee implemented for NIFTY as of now.')

        current_date = from_date
        total_pnl = 0

        while current_date <= to_date:
            LOGGER.info('Processing for %s' % current_date)

            if current_date.weekday() in [5, 6]:
                LOGGER.info('Found weekend %s, not trading...' % current_date)

                current_date += timedelta(days=1)

                continue

            traded_options: List[HistoricalOptionModel] = self._enter_market(option_gap=nifty_option_gap, on_date=current_date)

            pnl = 0

            for option in traded_options:
                pnl += (option.open - option.close) * option.lot_size

            if pnl < self.config.stoploss_pnl:
                pnl = self.config.stoploss_pnl

            total_pnl += pnl

            LOGGER.info('PnL for %s: %.2f' % (current_date, pnl))
            LOGGER.info('------------------------------------------------')

            current_date += timedelta(days=1)

        LOGGER.info('Total PnL: %.2f' % total_pnl)

    def _get_trading_width(self, tickersymbol: str):
        today = datetime.today()

        candles = InstrumentsController.get_instrument_candles(tickersymbol=tickersymbol, from_date=today - timedelta(days=365), to_date=today)

        candle_deviations = { 'up': [], 'down': [] }

        for candle in candles:
            candle_deviations['up'].append((candle.high - candle.open) / candle.open * 100)
            candle_deviations['down'].append((candle.open - candle.low) / candle.open * 100)

        up_90_percentile = numpy.percentile(candle_deviations['up'], 90)
        down_90_percentile = numpy.percentile(candle_deviations['down'], 90)

        return numpy.mean([up_90_percentile, down_90_percentile])

    def get_config_old(self) -> ConfigModel:
        questions = [
            {
                'type': 'list',
                'name': 'tickersymbol',
                'message': 'List of stocks to be processed!',
                'choices': [
                    { 'name': 'BANKNIFTY' }
                ]
            }
        ]

        tickersymbol = prompt(questions=questions, style=STYLE)['tickersymbol']
        default_strangle_width = self._get_trading_width(tickersymbol=tickersymbol)

        questions = [
            {
                'type': 'input',
                'name': 'strangle_width',
                'message': 'Width of strangle in percentage',
                'default': '%.2f' % default_strangle_width
            },
            {
                'type': 'input',
                'name': 'validity_in_days',
                'message': 'Validity of the position (in days)',
                'default': str(1)
            }
        ]

        config = prompt(questions=questions, style=STYLE)
        config['tickersymbol'] = tickersymbol
        config['strangle_width'] = float(config['strangle_width'])
        config['validity_in_days'] = int(config['validity_in_days'])

        return from_dict(data_class=ConfigModel, data=config)

    def run_custom_strangle(self):
        # Do the following:
        # 1. Get the market time of the day and work b/w 9.30-10.00AM
        # 2. Figure out the options to strangle with
        # 3. Get the strangle options
        # 4. Move out of the position at the end of the day
        config = self.get_config_old()

        if config.tickersymbol != 'BANKNIFTY':
            raise NotImplementedError('Option gap is hard-coded as 100, please implement the same for other stocks...')

        banknifty_option_gap = 100
        today = datetime.today()

        instrument_price = InstrumentsController.get_instrument_price_details(tickersymbol=config.tickersymbol).close

        low_sell_price = Utilities.round_nearest(number=instrument_price * (1 - config.strangle_width / 100), unit=banknifty_option_gap, direction='down')
        high_sell_price = Utilities.round_nearest(number=instrument_price * (1 + config.strangle_width / 100), unit=banknifty_option_gap, direction='up')

        instrument = InstrumentsController.get_instrument(tickersymbol=config.tickersymbol)

        options = InstrumentsController.get_options_chain(instrument=instrument)
        options_dict = dict((option.tradingsymbol, option) for option in options)

        next_thursday = Utilities.get_next_closest_thursday(dt=today)

        high_option = options_dict['%s%s%sCE' % (config.tickersymbol, re.sub('[a-z]', '', next_thursday.strftime(OPTIONS_TICKERSYMBOL_DATETIME_FORMAT)), high_sell_price)]
        low_option = options_dict['%s%s%sPE' % (config.tickersymbol, re.sub('[a-z]', '', next_thursday.strftime(OPTIONS_TICKERSYMBOL_DATETIME_FORMAT)), low_sell_price)]

        print('High option: ', high_option)
        print('Low option: ', low_option)

        # TODO: Add the time based trigger to buy and move out of the position at the end of the day
