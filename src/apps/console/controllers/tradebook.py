from datetime import date
from time import sleep
from typing import List
from dacite import from_dict
import requests

from src.apps.settings.controllers.config import ConfigController
from src.apps.console.models.tradebook import Trade

DATETIME_FORMAT = '%Y-%m-%d'
STATE_PENDING = 'PENDING'


class TradebookController:
    @staticmethod
    def get_trades(from_date: date, to_date: date, segment: str = 'EQ') -> List[Trade]:
        state = STATE_PENDING
        page = 1
        total_pages = 1
        trades = []

        while state == STATE_PENDING or page <= total_pages:
            url = 'https://console.zerodha.com/api/reports/tradebook?segment=%(segment)s&from_date=%(from_date)s&to_date=%(to_date)s&page=%(page)s&sort_by=order_execution_time&sort_desc=false' % {
                'segment': segment,
                'from_date': from_date.strftime(DATETIME_FORMAT),
                'to_date': to_date.strftime(DATETIME_FORMAT),
                'page': page
            }
            headers = {
                'x-csrftoken': ConfigController.get_config().zerodha_x_csrf_token,
                'cookie': 'session=%s;' % ConfigController.get_config().console_session
            }

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise ValueError('Failed to get the tradebook details from Zerodha')

            resp_json = response.json()
            state = resp_json['data']['state']

            if state == STATE_PENDING:
                sleep(2)

                continue

            total_pages = resp_json['data']['pagination']['total_pages']
            page += 1

            data = resp_json['data']['result']

            trades += [from_dict(data_class=Trade, data=trade) for trade in data]

        return trades
