from dataclasses import asdict
from typing import List

import requests
from dacite import from_dict

from src.apps.settings.controllers import ConfigController

from ..models import OrderModel, PlaceOrderModel
from .users import UsersController


class OrdersController:
    @staticmethod
    def get_orders(filter_is_open: bool = False) -> List[OrderModel]:
        response = requests.get(
            'https://kite.zerodha.com/oms/orders',
            headers={
                'Authorization': f'enctoken {ConfigController.get_config().kite_auth_token}'
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        orders = response.json()['data']

        orders = [from_dict(data_class=OrderModel, data=order) for order in orders]

        if filter_is_open:
            orders = [order for order in orders if order.is_open]

        return orders

    @staticmethod
    def place_order(order: PlaceOrderModel):
        if not isinstance(order, PlaceOrderModel):
            order = from_dict(data_class=PlaceOrderModel, data=order)

        order.user_id = UsersController.get_current_user().user_id

        response = requests.post(
            'https://kite.zerodha.com/oms/orders/regular',
            headers={
                'Authorization': f'enctoken {ConfigController.get_config().kite_auth_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data=asdict(order)
        )

        if response.status_code == 403:
            ConfigController.refresh_kite_enctoken()

            return OrdersController.place_order(order=order)

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))
