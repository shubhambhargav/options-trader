import traceback
import re

from datetime import datetime, date, timedelta
from typing import List

from src.apps.gsheets.controllers.symbols_list import SymbolsListController
from src.apps.questrade.controllers.options import OptionsController
from src.apps.questrade.controllers.symbols import SymbolsController
from src.apps.questrade.controllers.accounts import AccountsController
from src.apps.telegram.controllers import TelegramController

from src.apps.questrade.models.symbols import SymbolModel
from src.apps.questrade.models.accounts import AccountBalanceModel
from src.apps.questrade.models.options import ChainPerStrikePriceModel
from src.apps.gsheets.models.symbols import SymbolModel as SymbolListItemModel
from src.apps.questrade.models.options import OptionQuoteModel

from src.apps.settings.controllers import ConfigController
from src.apps.questrade.client import QuestradeClient
from src.logger import LOGGER

Q = QuestradeClient()

EXPIRY_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'

OPTIONS_MULTIPLIER = 100
OPTIONS_FILTER = {
    'expiry_in_days': 120,
    'minimum_price_drop_percentage': -10,
    'maximum_price_drop_percentage': -20,  # to avoid making API call for non-traded options
    'minimum_return_percentage': 0.85,  # to ensure 10-12% return per year
    'minimum_credit_value': 120,  # in USD to ensure that each trade accounts for commissions and give at least 100 USD in returns
    'maximum_last_price_change_percentage': 5,
    'maximum_put_positions_for_underlying': 4
}
SYMBOLS_FILTER = {
    'maximum_above_intrinsic_value': 30,  # Not investing in symbols which are more than 30% above the intrinsic value
    'maximum_entry_point_from_last_support': 30
}
ACCOUNT_FILTER = {
    'minimum_buying_power': 12000  # in USD
}

PUT_OPTION_SYMBOL_REGEX = re.compile('(?P<symbol>[a-zA-Z]+)(?P<expiry>[0-9]{1,2}[A-z]{3}[0-9]{2})P(?P<strike_price>[0-9.]+)')
EXTRACTED_EXPIRY_DATE_FORMAT = '%d%b%y'


def parse_option_symbol(symbol) -> dict:
    matched = PUT_OPTION_SYMBOL_REGEX.match(symbol)

    if not matched:
        return {}

    return matched.groupdict()


class OptionsSellerQuestrade:
    def _get_filtered_options(self, symbol: SymbolModel):
        options = OptionsController.get_options(symbol_id=symbol.symbolId)

        filtered_options: List[ChainPerStrikePriceModel] = []
        today: datetime = datetime.now()

        for option in options:
            expiry_date: datetime = datetime.strptime(option.expiryDate, EXPIRY_TIMESTAMP_FORMAT).replace(tzinfo=None)

            diff_days = (expiry_date - today).days

            if diff_days > OPTIONS_FILTER['expiry_in_days']:
                continue

            for option_root in option.chainPerRoot:
                for option_strike in option_root.chainPerStrikePrice:
                    diff_price = (option_strike.strikePrice - symbol.prevDayClosePrice) / symbol.prevDayClosePrice * 100

                    if diff_price > OPTIONS_FILTER['minimum_price_drop_percentage'] or diff_price < OPTIONS_FILTER['maximum_price_drop_percentage']:
                        continue

                    filtered_options.append(option_strike)

        LOGGER.info(f'Found {len(filtered_options)} options for {symbol.symbol} to fetch the prices for')

        option_quotes = OptionsController.get_option_quotes(
            # ids=[option.callSymbolId for option in options[0].chainPerRoot[0].chainPerStrikePrice[:3]]
            ids=[option.putSymbolId for option in filtered_options]
        )

        filtered_options = []

        for option in option_quotes:
            if not option.lastTradePrice:
                LOGGER.info(f'Last trade price not found, hence skipping option: {option.symbol}')

                continue

            if option.askPrice:
                last_price_diff_percentage = (option.lastTradePrice - option.askPrice) / option.lastTradePrice * 100

                if last_price_diff_percentage > OPTIONS_FILTER['maximum_last_price_change_percentage']:
                    continue

            option_price = option.askPrice if option.askPrice else option.lastTradePrice
            total_credit = option_price * OPTIONS_MULTIPLIER

            if total_credit < OPTIONS_FILTER['minimum_credit_value']:
                LOGGER.info(f'Skipping option {option.symbol} due to less credit: {round(total_credit, 2)}')

                continue

            symbol_data = parse_option_symbol(symbol=option.symbol)
            strike_price = float(symbol_data['strike_price'])
            expiry_date = datetime.strptime(symbol_data['expiry'], EXTRACTED_EXPIRY_DATE_FORMAT)

            date_diff_month = ((expiry_date - today).days) / 30  # 30 being days in a month

            percentage_return = ((option_price / strike_price) * 100) / date_diff_month

            if percentage_return < OPTIONS_FILTER['minimum_return_percentage']:
                LOGGER.info(f'Skipping option {option.symbol} due to less return: {round(percentage_return, 2)}')
                LOGGER.info(f'Details: Option price: {option_price}, strike price: {strike_price}, total return: {round(total_credit, 2)}, days left in expiry: {round(date_diff_month, 2)}')

                continue

            filtered_options.append(option)

        return filtered_options

    def _get_filtered_symbols(self, symbols_list: List[SymbolListItemModel]) -> List[SymbolModel]:
        filtered_symbols_list = []

        for symbol in symbols_list:
            if not symbol.is_active:
                LOGGER.info(f'Skipping symbol {symbol.symbol} because it is not active')

                continue

            if symbol.percentage > SYMBOLS_FILTER['maximum_above_intrinsic_value']:
                LOGGER.info(f'Skipping symbol {symbol.symbol} because it is too much above intrinsic value, expected {SYMBOLS_FILTER["maximum_above_intrinsic_value"]}, found: {symbol.percentage}')

                continue

            filtered_symbols_list.append(symbol)

        LOGGER.info(f'Retrieved {len(filtered_symbols_list)} symbols to process')

        symbols = self._get_symbols(symbols_list=filtered_symbols_list)

        filtered_enriched_symbols = []

        enriched_symbols = SymbolsController.enrich_symbols(symbols=symbols)

        for symbol in enriched_symbols:
            # Skip the symbols which:
            #   - are already trading below last support because we don't know how low can they get
            #       - this may be invalid once we introduce fundamental / intrinsic value and willing to buy the stock beyond that
            #       # TODO for the above
            #   - have already reached the last resistance i.e. no expected room to grow, hence they will potentially drop and introduce a risk on selling PUTs
            if symbol.close_last_by_resistance is None or symbol.close_last_by_support is None:
                LOGGER.info(
                    'Skipping symbol %s because insufficient data found: last support: %s, last resistance: %s' % (
                        symbol.symbol, symbol.close_last_by_support, symbol.close_last_by_resistance
                    )
                )

                continue

            if symbol.close_last_by_support < 0 or symbol.close_last_by_resistance > 0:
                LOGGER.info(
                    'Skipping instrument %s because of -ve support or +ve resistance from close: %.2f last support and %.2f last resistance' % (
                        symbol.symbol, symbol.close_last_by_support, symbol.close_last_by_resistance
                    )
                )

                continue

            support_resistance_gap = symbol.close_last_by_support + abs(symbol.close_last_by_resistance)

            percentage_up_from_support = symbol.close_last_by_support / support_resistance_gap * 100

            if percentage_up_from_support > SYMBOLS_FILTER['maximum_entry_point_from_last_support']:
                LOGGER.info(
                    'Skipping symbol %s because the stock has already moved by %d percent from last support' % (
                        symbol.symbol, percentage_up_from_support
                    )
                )

                continue

            filtered_enriched_symbols.append(symbol)

        filtered_enriched_symbols = set([symbol.symbol for symbol in  filtered_enriched_symbols])

        filtered_symbols = [symbol for symbol in symbols if symbol.symbol in filtered_enriched_symbols]

        return filtered_symbols

    def _get_symbols(self, symbols_list: List[SymbolListItemModel]) -> List[SymbolModel]:
        symbols = []

        for symbol_list_item in symbols_list:
            symbol_base = SymbolsController.find_symbol(name=symbol_list_item.symbol)
            symbol = SymbolsController.get_symbol(id=symbol_base.symbolId)

            symbols.append(symbol)

        return symbols

    def _get_available_buying_power(self) -> float:
        account_currencies: List[AccountBalanceModel] = AccountsController.get_balances(account_id=ConfigController.get_config().questrade_account_id)
        usd_balance = {}

        for currency in account_currencies:
            if currency.currency == 'USD':
                usd_balance = currency

        return usd_balance.maintenanceExcess

    def _filter_existing_positions(self, options: List[OptionQuoteModel]):
        account_id = ConfigController.get_config().questrade_account_id

        positions = AccountsController.get_positions(account_id=account_id)
        orders = AccountsController.get_orders(account_id=account_id)

        positions_set = set([position.symbol for position in positions] + [order.symbol for order in orders])

        underlying_option_count = {}

        for position_symbol in positions_set:
            parsed_symbol = parse_option_symbol(symbol=position_symbol)

            if not parsed_symbol:
                continue

            if underlying_option_count.get(parsed_symbol['symbol']):
                underlying_option_count[parsed_symbol['symbol']] += 1
            else:
                underlying_option_count[parsed_symbol['symbol']] = 1

        filtered_options = []

        for option in options:
            if option.symbol in positions_set:
                LOGGER.info(f'Removing option {option.symbol} from the recommendations since there is an already existing position')

                continue

            parsed_option_symbol = parse_option_symbol(symbol=option.symbol)['symbol']

            if underlying_option_count.get(parsed_option_symbol) >= OPTIONS_FILTER['maximum_put_positions_for_underlying']:
                LOGGER.info(f'Skipping recommending option {option.symbol} because there are already {underlying_option_count.get(parsed_option_symbol)} positions/orders for the underlying')

                continue

            filtered_options.append(option)

        return filtered_options

    def _filter_based_on_margin(self, margin: float, options: List[OptionQuoteModel], symbols_list: List[SymbolListItemModel]) -> List[OptionQuoteModel]:
        symbols_dict = dict((symbol.symbol, symbol) for symbol in symbols_list)

        filtered_options = []

        for option in options:
            parsed_option_symbol = parse_option_symbol(symbol=option.symbol)

            symbol = symbols_dict[parsed_option_symbol['symbol']]
            margin_required = symbol.long_mr * float(parsed_option_symbol['strike_price']) * OPTIONS_MULTIPLIER / 100

            margin -= margin_required

            if margin < ACCOUNT_FILTER['minimum_buying_power']:
                message = f'Skipping the recommendation {option.symbol} because the updated margin {margin} is below the minimum margin {ACCOUNT_FILTER["minimum_buying_power"]}'

                LOGGER.info(message)

                TelegramController.send_message(message=message)

                break

            filtered_options.append(option)

        return filtered_options

    def _construct_message(self, options: List[OptionQuoteModel]) -> str:
        message = 'Option\tProfit\n'

        for option in options:
            message += f'{option.symbol}\t{option.lastTradePrice * OPTIONS_MULTIPLIER}\n'

        return message

    def run(self):
        # TODO
        # Add the following filters:
        # 1. [Done] Stock filter based on fundamental value
        # 2. [Done] Stock filter based on last support and resistance
        # 3. [Done] Filter based on already existing positions
        # 4. [Done] Filter based on margin available or margin required
        # 4.1 Start running the engine on the server
        # 5. Add awareness of earnings / dividends date
        # 6. Create an enriched option with all the information to be printed / sent / stored
        # 7. Figure out a way to create link for Questrade account single click trade
        options_of_interest = []

        try:
            buying_power = self._get_available_buying_power()

            if buying_power < ACCOUNT_FILTER['minimum_buying_power']:
                message = f'Not recommending since the buying power is less than required. Found: {buying_power}, required: {ACCOUNT_FILTER["minimum_buying_power"]}'

                TelegramController.send_message(message=message)

                LOGGER.info(message)

                Q.destroy()

                return

            LOGGER.info(f'options_selling_questrade~run: Available buying power: {buying_power}')

            symbols_list = SymbolsListController.get_symbols_list()
            filtered_symbols = self._get_filtered_symbols(symbols_list=symbols_list)

            LOGGER.info(f'options_selling_questrade~run: Filtered symbol count: {len(filtered_symbols)}')

            for symbol in filtered_symbols:
                filtered_options = self._get_filtered_options(symbol=symbol)

                if filtered_options:
                    options_of_interest.extend(filtered_options)

            options_of_interest = self._filter_existing_positions(options=options_of_interest)

            # TODO: Figure out the right sorting for the options
            options_of_interest = self._filter_based_on_margin(margin=buying_power, options=options_of_interest, symbols_list=symbols_list)

            # TODO: Print options of interest in human readable fashion
            LOGGER.info(f'Filtered the option count to: {len(options_of_interest)}')

            message = self._construct_message(options=options_of_interest)

            TelegramController.send_message(message=message)
        except Exception as ex:
            traceback.print_exc()

        Q.destroy()
