from typing import List

from dacite import from_dict

from ..models.accounts import AccountBalanceModel, PositionModel, OrderModel
from ..client import QuestradeClient

from src.logger import LOGGER

Q = QuestradeClient().initialize()


class AccountsController:
    @staticmethod
    def get_balances(account_id: str) -> List[AccountBalanceModel]:
        balances = []

        for balance in Q.account_balances(id=account_id)['perCurrencyBalances']:
            balances.append(from_dict(data_class=AccountBalanceModel, data=balance))

        return balances

    @staticmethod
    def get_positions(account_id: str) -> List[PositionModel]:
        positions = []

        positions_resopnse = Q.account_positions(id=account_id)['positions']

        for position in positions_resopnse:
            positions.append(from_dict(data_class=PositionModel, data=position))

        return positions

    @staticmethod
    def get_orders(account_id: str) -> List[OrderModel]:
        orders_response = Q.account_orders(id=account_id)

        orders = []

        for order in orders_response['orders']:
            orders.append(from_dict(data_class=OrderModel, data=order))

        return orders
