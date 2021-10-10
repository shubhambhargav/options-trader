import re
from datetime import datetime, timedelta

import numpy
from PyInquirer import Token, prompt, style_from_dict
from dacite.core import from_dict

from src.apps.kite.controllers import InstrumentsController
from src.strategies.strangling.models import ConfigModel
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


class Strangler:
    def __init__(self):
        pass

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

    def get_config(self) -> ConfigModel:
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

    def run(self):
        # Do the following:
        # 1. Get the market time of the day and work b/w 9.30-10.00AM
        # 2. Figure out the options to strangle with
        # 3. Get the strangle options
        # 4. Move out of the position at the end of the day
        config = self.get_config()

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
