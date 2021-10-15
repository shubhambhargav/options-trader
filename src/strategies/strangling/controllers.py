import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import numpy
from PyInquirer import Token, prompt, style_from_dict
from dacite.core import from_dict

from src.apps.kite.connectors.websocket import KiteTicker
from src.apps.kite.controllers.positions import PositionsController
from src.apps.kite.controllers.instruments import InstrumentsController
from src.apps.kite.controllers.options import OptionsController
from src.apps.kite.controllers.users import UsersController
from src.apps.settings.controllers.config import ConfigController
from src.strategies.strangling.models import ConfigModel, ConfigV2Model
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

POSITIONS = []
GLOBAL_CONFIG = None


def on_ticks(ws, ticks):
    # Callback to receive ticks.
    LOGGER.info('Ticks: {}'.format(ticks))
    # TODO: Add the check for the stoploss and exit the trade


def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    # TODO: Add the instrument token fetcher based on tickersymbol
    ws.subscribe([738561, 5633])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [738561])


def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()


class Strangler:
    def __init__(self, config: ConfigV2Model = None):
        self.config = config

    def _enter_market(self, option_gap: int):
        global POSITIONS

        tickersymbol = self.config.tickersymbol
        strangle_gap = self.config.strangle_gap

        today = datetime.today()

        # TODO: Verify if the following works correctly
        instrument_price = InstrumentsController.get_last_trading_price(tickersymbol=tickersymbol)

        low_sell_price = Utilities.round_nearest(number=instrument_price - strangle_gap, unit=option_gap, direction='down')
        high_sell_price = Utilities.round_nearest(number=instrument_price + strangle_gap, unit=option_gap, direction='up')

        instrument = InstrumentsController.get_instrument(tickersymbol=tickersymbol)
        options = InstrumentsController.get_options_chain(instrument=instrument)
        options_dict = dict((option.tradingsymbol, option) for option in options)

        print(','.join([elem for elem in options_dict.keys()]))

        next_thursday = Utilities.get_next_closest_thursday(dt=today)

        high_option = options_dict['%s%s%sCE' % (tickersymbol, next_thursday.strftime(STOCK_OPTIONS_TICKERSYMBOL_DATETIME_FORMAT).upper(), high_sell_price)]
        low_option = options_dict['%s%s%sPE' % (tickersymbol, next_thursday.strftime(STOCK_OPTIONS_TICKERSYMBOL_DATETIME_FORMAT).upper(), low_sell_price)]

        if self.config.is_mock_run:
            POSITIONS += [high_option, low_option]

            return POSITIONS

        OptionsController.sell_option(option=high_option)
        OptionsController.sell_option(option=low_option)

        positions = PositionsController.get_positions()

        for position in positions:
            if position.tradingsymbol in [high_option.tradingsymbol, low_option.tradingsymbol]:
                POSITIONS.append(position)

        return POSITIONS

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
                'message': 'Gap of strangle in units',
                'default': '200'
            },
            {
                'type': 'input',
                'name': 'stoploss_pnl',
                'message': 'Stoploss PnL',
                'default': '1000'
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
        if not self.config:
            self.config = self.get_config()

        global GLOBAL_CONFIG

        GLOBAL_CONFIG = self.config

        # Following code has hard-coded values as of now
        # TODO: Make the values configurable
        # TODO (overall):
        #       - Make cookie generation configurable
        #       - Add automatic cookie generation
        #       - Add stoploss execution
        #       - Add websocket subscription for instruments
        #       - Add logging for sample run
        # TODO (later): Figure out how to account for token refresh in-between
        nifty_option_gap = 100
        now = datetime.now()

        if self.config.tickersymbol != 'NIFTY':
            raise NotImplementedError('The program has only bee implemented for NIFTY as of now.')

        if now.weekday() not in [0, 1, 2, 3, 4]:
            LOGGER.info('Found weekend, not trading...')

            return

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
