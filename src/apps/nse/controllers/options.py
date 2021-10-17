from typing import List
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from dacite import from_dict

from src.cache import Cache
from src.apps.nse.models.options import HistoricalOptionModel

EXPIRY_DATE_FORMAT = '%d-%m-%Y'
FROM_TO_DATE_FORMAT = '%d-%m-%Y'

FLOAT_FIELDS = set(['strike_price', 'open', 'high', 'low', 'close', 'ltp', 'settle_price', 'open_int'])


class OptionsController:
    # @Cache
    @staticmethod
    def get_historical_data(tickersymbol: str, expiry_date: date, strike_price: float = '', option_types: str = ['PE', 'CE'], from_date: date = None, to_date: date = None) -> List[HistoricalOptionModel]:
        if not from_date:
            from_date = expiry_date - timedelta(days=7)

        if not to_date:
            to_date = expiry_date

        data = []
        instrument_type_map = {
            'BANKNIFTY': 'OPTIDX',
            'NIFTY': 'OPTIDX',
            'default': 'OPTSTK'
        }

        for option_type in option_types:
            url = 'https://www1.nseindia.com/products/dynaContent/common/productsSymbolMapping.jsp?instrumentType=%(instrument_type)s&symbol=%(tickersymbol)s&expiryDate=%(expiry_date)s&optionType=%(option_type)s&strikePrice=%(strike_price)s&dateRange=&fromDate=%(from_date)s&toDate=%(to_date)s&segmentLink=9&symbolCount=' % {
                'instrument_type': instrument_type_map.get(tickersymbol, instrument_type_map['default']),
                'tickersymbol': tickersymbol,
                'option_type': option_type,
                'strike_price': str(strike_price),
                'expiry_date': expiry_date.strftime(EXPIRY_DATE_FORMAT),
                'from_date': from_date.strftime(FROM_TO_DATE_FORMAT),
                'to_date': to_date.strftime(FROM_TO_DATE_FORMAT)
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
                'Referer': 'https://www1.nseindia.com/products/content/derivatives/equities/historical_fo.htm'
            }

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

            soup = BeautifulSoup(response.text, 'html.parser')

            csv_content = soup.find('div', {'id': 'csvContentDiv'})

            if not csv_content:
                continue

            csv_content = csv_content.get_text()
            lines = csv_content.split(':')

            headers = lines[0].lower().strip() \
                .replace('"', '').replace(' ', '_').replace('.', '') \
                .split(',')

            for line in lines[1:]:
                if not line:
                    continue

                content = line.strip().replace('"', '').split(',')
                content = dict(zip(headers, content))

                content = dict((k, float(v) if k in FLOAT_FIELDS else v) for k, v in content.items())
                content['instrument_type'] = option_type
                content['underlying_instrument'] = tickersymbol

                data.append(from_dict(data_class=HistoricalOptionModel, data=content))

        return data
