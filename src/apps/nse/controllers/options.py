from typing import List
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from dacite import from_dict

from src.apps.nse.models.options import HistoricalOptionModel

EXPIRY_DATE_FORMAT = '%d-%m-%Y'
FROM_TO_DATE_FORMAT = '%d-%b-%Y'


class OptionsController:
    @staticmethod
    def get_historical_data(tickersymbol: str, option_type: str, expiry_date: date, from_date: date = None, to_date: date = None) -> List[HistoricalOptionModel]:
        if not from_date:
            from_date = expiry_date - timedelta(days=7)

        if not to_date:
            to_date = expiry_date - timedelta(days=7)

        url = 'https://www1.nseindia.com/products/dynaContent/common/productsSymbolMapping.jsp?instrumentType=OPTIDX&symbol=%(tickersymbol)s&expiryDate=%(expiry_date)s&optionType=%(option_type)s&strikePrice=&dateRange=&fromDate=%(from_date)s&toDate=%(to_date)s&segmentLink=9&symbolCount=' % {
            'tickersymbol': tickersymbol,
            'option_type': option_type,
            'expiry_date': expiry_date.strftime(EXPIRY_DATE_FORMAT),
            'from_date': from_date.strftime(FROM_TO_DATE_FORMAT),
            'to_date': to_date.strftime(FROM_TO_DATE_FORMAT)
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        soup = BeautifulSoup(response.text, 'html.parser')

        csv_content = soup.find('div', {'id': 'csvContentDiv'}).get_text()
        lines = csv_content.split(':')
        data = []

        headers = lines[0].lower().strip() \
            .replace('"', '').replace(' ', '_').replace('.', '') \
            .split(',')

        for line in lines[1:]:
            if not line:
                continue

            content = line.strip().replace('"', '').split(',')

            data.append(from_dict(data_class=HistoricalOptionModel, data=dict(zip(headers, content))))

        return data
