import requests
from typing import List, Optional

from dacite import from_dict

import src.utilities as Utilities
from src.apps.kite.models.orders import EXCHANGE_NSE, PRODUCT_CNC, PlaceOrderModel, TRANSACTION_TYPE_SELL
from src.apps.settings.controllers import ConfigController
from src.apps.kite.controllers.orders import OrdersController
from src.logger import LOGGER

from ..models import HoldingModel


class HoldingsController:
    @staticmethod
    def get_holdings() -> List[HoldingModel]:
        response = requests.get(
            'https://kite.zerodha.com/oms/portfolio/holdings',
            headers={
                'Authorization': f'enctoken {ConfigController.get_config().kite_auth_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        holdings = response.json()['data']

        return [from_dict(data_class=HoldingModel, data=holding) for holding in holdings]

    @staticmethod
    def get_holding(tradingsymbol: str) -> Optional[HoldingModel]:
        holdings = HoldingsController.get_holdings()

        for holding in holdings:
            if holding.tradingsymbol == tradingsymbol:
                return holding

        return None

    @staticmethod
    def exit_holding(holding: HoldingModel):
        order = {
            'tradingsymbol': holding.tradingsymbol,
            'transaction_type': TRANSACTION_TYPE_SELL,
            'quantity': holding.quantity,
            'price': Utilities.round_nearest(number=holding.last_price + 0.05, unit=0.05),
            'product': PRODUCT_CNC,
            'exchange': EXCHANGE_NSE
        }

        OrdersController.place_order(order=from_dict(data_class=PlaceOrderModel, data=order))

        LOGGER.info('Successfully placed exit order for %s...' % holding.tradingsymbol)
