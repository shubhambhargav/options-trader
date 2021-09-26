from datetime import date, timedelta

from PyInquirer import Token, prompt, style_from_dict
from dacite import from_dict

import src.utilities as Utilities
from src.apps.nse.controllers.options import OptionsController
from src.apps.kite.controllers.instruments import InstrumentsController
from src.strategies.iron_candor.models import ConfigModel
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


class BackTester:
    def __init__(self):
        pass

    def get_config(self) -> ConfigModel:
        questions = [
            {
                'type': 'checkbox',
                'name': 'tickers',
                'message': 'List of tickers to be processed!',
                'choices': [
                    { 'name': 'BANKNIFTY' }
                ]
            }
        ]

        config = prompt(questions=questions, style=STYLE)

        return from_dict(data_class=ConfigModel, data=config)

    def run(self):
        # config = self.get_config()
        config = from_dict(data_class=ConfigModel, data={'tickers': ['BANKNIFTY']})

        ## To be put into a configuration
        delta_expectation = 5  # in percentage

        start_date = date(2021, 3, 11)
        end_date = date(2021, 9, 23)
        iteration_date = start_date
        tickersymbol = config.tickers[0]
        lot_size = 40
        iteration_count = 0
        max_iteration_count = 20
        total_expected_pnl = 0
        total_pnl = 0

        skip_week = [
            date(2021, 3, 11), date(2021, 3, 18), date(2021, 5, 13), date(2021, 5, 20),
            date(2021, 8, 19), date(2021, 8, 26)
        ]

        while iteration_date < end_date:
            if iteration_date in skip_week:
                iteration_date += timedelta(days=7)

                continue

            position_date = iteration_date - timedelta(days=7)

            instrument_price = InstrumentsController.get_instrument_price_details(
                tickersymbol=tickersymbol,
                date_val=position_date
            ).close

            print('Price for BANKNIFTY on %s is: %s' % (iteration_date, instrument_price))

            low_sell_price = Utilities.round_nearest(number=instrument_price * (1 - delta_expectation / 100), unit=100)
            high_sell_price = Utilities.round_nearest(number=instrument_price * (1 + delta_expectation / 100), unit=100)

            options_data = OptionsController.get_historical_data(
                tickersymbol=tickersymbol,
                expiry_date=iteration_date,
                from_date=position_date,
                to_date=position_date
            )

            option_strike_price_dict = dict((option.option_type + str(int(option.strike_price)), option) for option in options_data)

            low_sell_option = option_strike_price_dict['PE' + str(low_sell_price)]
            low_buy_option = option_strike_price_dict['PE' + str(low_sell_price - 100)]
            high_sell_option = option_strike_price_dict['CE' + str(high_sell_price)]
            high_buy_option = option_strike_price_dict['CE' + str(high_sell_price + 100)]

            # print(low_buy_option)
            # print(low_sell_option)
            # print(high_sell_option)
            # print(high_buy_option)

            expected_max_profit = (low_sell_option.close + high_sell_option.close - low_buy_option.close - high_buy_option.close) * lot_size
            total_expected_pnl += expected_max_profit

            print('Expected max profit: %.2f' % expected_max_profit)

            expiry_day_instrument_price = InstrumentsController.get_instrument_price_details(
                tickersymbol=tickersymbol,
                date_val=iteration_date
            ).close

            expiry_options_data = OptionsController.get_historical_data(
                tickersymbol=tickersymbol,
                expiry_date=iteration_date,
                from_date=iteration_date,
                to_date=iteration_date
            )

            expiry_option_strike_price_dict = dict((option.option_type + str(int(option.strike_price)), option) for option in expiry_options_data)

            expiry_low_sell_option = expiry_option_strike_price_dict['PE' + str(low_sell_price)]
            expiry_low_buy_option = expiry_option_strike_price_dict['PE' + str(low_sell_price - 100)]
            expiry_high_sell_option = expiry_option_strike_price_dict['CE' + str(high_sell_price)]
            expiry_high_buy_option = expiry_option_strike_price_dict['CE' + str(high_sell_price + 100)]

            pnl = (
                (low_sell_option.close + high_sell_option.close) -
                    (expiry_low_sell_option.close + expiry_high_sell_option.close) -
                (low_buy_option.close + high_buy_option.close) +
                    (expiry_low_buy_option.close + expiry_high_buy_option.close)
            ) * lot_size

            # print(expiry_low_buy_option)
            # print(expiry_low_sell_option)
            # print(expiry_high_sell_option)
            # print(expiry_high_buy_option)

            print('Final pnl achieved: %.2f' % pnl)

            total_pnl += pnl

            price_percentage_change = (expiry_day_instrument_price - instrument_price) / instrument_price * 100
            print('Price change happened: %.2f percent' % price_percentage_change)

            print('----------------------------')

            iteration_date += timedelta(days=7)

            iteration_count += 1

            if iteration_count >= max_iteration_count:
                break

        print('-------------------')
        print('Total expected pnl: %.2f' % total_expected_pnl)
        print('Final pnl achieved: %.2f' % total_pnl)
