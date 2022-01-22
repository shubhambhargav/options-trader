from dataclasses import dataclass
from datetime import date
from typing import Dict

from dacite import from_dict


class ZerodhaEquityTransactionCharges:
    # All values are in percentage of the transaction
    STT = 0.1
    TRANSACTION_CHARGES = 0.00345
    GST = 18
    SEBI = 0.0001
    STAMP_CHARGES = 0.015


@dataclass
class HolidayAlernateModel:
    option_expiry: date


@dataclass
class OptionData:
    margin_backup_ratio: float
    lot_size: int


MARKET_HOLIDAYS_ALTERNATES: Dict[date, HolidayAlernateModel] = {
    date(2021, 10, 15): from_dict(
        data_class=HolidayAlernateModel,
        data={
            'option_expiry': date(2021, 10, 14)
        }
    )
}

# Following have been taken as static values since the data is not publicly avaiable
# margin calculation is primarily taken as a percentage of backup money of current data
OPTION_DATA_MAP = {
    'NIFTY': { 'margin_backup_ratio': 1/8, 'lot_size': 50 },
    'ASIANPAINT': { 'margin_backup_ratio': 1/8, 'lot_size': 300 },
    'BANDHANBNK': { 'margin_backup_ratio': 1/2.6, 'lot_size': 1800 },
    'BHARTIARTL': { 'margin_backup_ratio': 1/5.5,  'lot_size': 1886 },
    'COALINDIA': { 'margin_backup_ratio': 1/6, 'lot_size': 4200 },
    'DRREDDY': { 'margin_backup_ratio': 1/9, 'lot_size': 125 },
    'HDFC': { 'margin_backup_ratio': 1/5.8, 'lot_size': 300 },
    'HDFCAMC': { 'margin_backup_ratio': 1/5.8, 'lot_size': 200 },
    'HDFCBANK': { 'margin_backup_ratio': 1/9, 'lot_size': 550 },
    'HEROMOTOCO': { 'margin_backup_ratio': 1/7, 'lot_size': 300 },
    'HINDUNILVR': { 'margin_backup_ratio': 1/8.5, 'lot_size': 300 },
    'ICICIBANK': { 'margin_backup_ratio': 1/7, 'lot_size': 1375 },
    'INFY': { 'margin_backup_ratio': 1/8.5, 'lot_size': 600 },
    'ITC': { 'margin_backup_ratio': 1/6, 'lot_size': 3200 },
    'KOTAKBANK': { 'margin_backup_ratio': 1/5.5, 'lot_size': 400 },
    'M&MFIN': { 'margin_backup_ratio': 1/5, 'lot_size': 4000 },
    'MARUTI': { 'margin_backup_ratio': 1/6, 'lot_size': 100 },
    'MRF': { 'margin_backup_ratio': 1/6, 'lot_size': 10 },
    'NESTLEIND': { 'margin_backup_ratio': 1/9, 'lot_size': 50 },
    'PVR': { 'margin_backup_ratio': 1/6, 'lot_size': 407 },
    'PIDILITIND': { 'margin_backup_ratio': 1/6, 'lot_size': 500 },
    'RELIANCE': { 'margin_backup_ratio': 1/6, 'lot_size': 250 },
    'TATACHEM': { 'margin_backup_ratio': 1/7, 'lot_size': 1000 },
    'TCS': { 'margin_backup_ratio': 1/7, 'lot_size': 300 },
    'TITAN': { 'margin_backup_ratio': 1/7, 'lot_size': 375 }
}
OPTION_DATA_MAP: Dict[str, OptionData] = dict((k, from_dict(data_class=OptionData, data=v)) for k, v in OPTION_DATA_MAP.items())

# Old ticker to new ticker
TICKER_CHANGE_MAP: Dict[str, str]  = {
    'ADANIGREEN-BE': 'ADANIGREEN',
    'ADANITRANS-BE': 'ADANITRANS'
}
