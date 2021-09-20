from dataclasses import asdict
from typing import List

import requests
from dacite import from_dict

from src._variables import VARIABLES

from ..models import OrderModel, PlaceOrderModel
from .users import UsersController


class OrdersController:
    @staticmethod
    def get_orders() -> List[OrderModel]:
        response = requests.get(
            'https://kite.zerodha.com/oms/orders',
            headers={
                'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        orders = response.json()['data']

        return [from_dict(data_class=OrderModel, data=order) for order in orders]

    @staticmethod
    def place_order(order: PlaceOrderModel):
        if not isinstance(order, PlaceOrderModel):
            order = from_dict(data_class=PlaceOrderModel, data=order)

        order.user_id = UsersController.get_current_user().user_id

        response = requests.post(
            'https://kite.zerodha.com/oms/orders/regular',
            headers={
                'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}",
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data=asdict(order)
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))
