from typing import List

from dacite import from_dict

import src.utilities as Utilities
from src.apps.kite.controllers.holdings import HoldingsController
from src.apps.kite.controllers.orders import OrdersController
from src.apps.kite.models.holdings import HoldingModel
from src.apps.kite.models.orders import PlaceOrderModel, TRANSACTION_TYPE_BUY, TRANSACTION_TYPE_SELL
from src.logger import LOGGER

EXPECTED_TAX_BRACKET = 30  # in percentage


class TaxHarvester:
    @staticmethod
    def harvest_tax():
        holdings = HoldingsController.get_holdings()
        holdings_to_transact: List[HoldingModel] = []

        for holding in holdings:
            if holding.average_price == 0:
                # This holding pertains to bonds or other entities which are in DEMAT form
                # but are not relevant for tax harvesting
                continue

            if holding.pnl > 0:
                continue

            if holding.tradingsymbol.startswith('SGB'):
                # Skipping gold bonds for tax harvesting as the probability of getting the gold bond
                # on the current market price is not high and multiple factors contribute to the
                # profitability of gold bonds
                continue

            expected_tax_advantage = abs(holding.pnl * EXPECTED_TAX_BRACKET / 100)
            expected_transaction_charges = holding.expected_transaction_charges

            if expected_tax_advantage > expected_transaction_charges:
                holdings_to_transact.append(holding)

                LOGGER.info('Holding: %s, transaction charges: %.2f, expected tax harvest: %.2f'% (
                    holding.tradingsymbol, holding.expected_transaction_charges, expected_tax_advantage
                ))

        required_funds = sum([holding.last_price * holding.quantity for holding in holdings_to_transact])
        expected_tax_harvest = (
            sum([abs(holding.pnl * EXPECTED_TAX_BRACKET / 100) for holding in holdings_to_transact]) -
            sum([holding.expected_transaction_charges for holding in holdings_to_transact])
        )

        LOGGER.info('Required funds: %.2f, expected total tax harvest: %.2f' % (required_funds, expected_tax_harvest))

        continue_input = input('Continue? (respond with Y/y) ')

        if not (continue_input == 'Y' or continue_input == 'y'):
            LOGGER.info('Exiting....')

            return

        for holding in holdings_to_transact:
            HoldingsController.exit_holding(holding=holding)

            order = {
                'tradingsymbol': holding.tradingsymbol,
                'transaction_type': TRANSACTION_TYPE_BUY,
                'quantity': holding.quantity,
                'price': Utilities.round_nearest(number=holding.last_price - 0.05, unit=0.05)
            }

            OrdersController.place_order(order=from_dict(data_class=PlaceOrderModel, data=order))

            LOGGER.info('Successfully placed entry order for %s...' % holding.tradingsymbol)

            break
