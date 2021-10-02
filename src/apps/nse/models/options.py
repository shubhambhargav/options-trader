from dataclasses import dataclass
from datetime import datetime
from src.apps.kite.models.orders import OrderModel
from src.apps.kite.models.positions import PositionModel
from src.apps.kite.models.instruments import EnrichedInstrumentModel, InstrumentModel
from typing import Any, List, Optional, Union

from dacite.core import from_dict

# Following have been taken as static values since the data is not publicly avaiable
# margin calculation is primarily taken as a percentage of backup money of current data
OPTION_DATA_MAP = {
    # TODO: Add ITC, MRF, PIDILITIND
    'ASIANPAINT': { 'margin_bckup_ratio': 1/8, 'lot_size': 300 },
    'BANDHANBANK': { 'margin_bckup_ratio': 1/2.6, 'lot_size': 1800 },
    'BHARTIARTL': { 'margin_bckup_ratio': 1/5.5,  'lot_size': 1886 },
    'COALINDIA': { 'margin_bckup_ratio': 1/6, 'lot_size': 4200 },
    'DRREDDY': { 'margin_bckup_ratio': 1/9, 'lot_size': 125 },
    'HDFC': { 'margin_bckup_ratio': 1/5.8, 'lot_size': 300 },
    'HDFCBANK': { 'margin_bckup_ratio': 1/9, 'lot_size': 550 },
    'HEROMOTOCO': { 'margin_bckup_ratio': 1/7, 'lot_size': 300 },
    'HINDUNILVR': { 'margin_bckup_ratio': 1/8.5, 'lot_size': 300 },
    'ICICIBANK': { 'margin_bckup_ratio': 1/7, 'lot_size': 1375 },
    'INFY': { 'margin_bckup_ratio': 1/8.5, 'lot_size': 600 },
    'KOTAKBANK': { 'margin_bckup_ratio': 1/5.5, 'lot_size': 400 },
    'M&MFIN': { 'margin_bckup_ratio': 1/5, 'lot_size': 4000 },
    'MARUTI': { 'margin_bckup_ratio': 1/6, 'lot_size': 100 },
    'NESTLEIND': { 'margin_bckup_ratio': 1/9, 'lot_size': 50 },
    'PVR': { 'margin_bckup_ratio': 1/6, 'lot_size': 407 },
    'RELIANCE': { 'margin_bckup_ratio': 1/6, 'lot_size': 250 },
    'TATACHEM': { 'margin_bckup_ratio': 1/7, 'lot_size': 1000 },
    'TCS': { 'margin_bckup_ratio': 1/7, 'lot_size': 300 },
    'TITAN': { 'margin_bckup_ratio': 1/7, 'lot_size': 375 }
}
OPTIONS_EXPIRY_DATETIME_FORMAT = '%d-%b-%Y'


@dataclass
class DefaultVal:
    val: Any


@dataclass
class HistoricalOptionMarginModel:
    total: float


@dataclass
class HistoricalOptionModel:
    symbol: str
    date: str
    expiry: str
    option_type: str
    strike_price: float
    open: float
    high: float
    low: float
    close: float
    ltp: float
    settle_price: float
    no_of_contracts: str
    turnover_in_lacs: str
    premium_turnover_in_lacs: str
    open_int: float
    change_in_oi: str
    underlying_value: str
    # Following are added within the controller itself to make this model compatible with
    # the corresponding Option model
    instrument_type: str
    underlying_instrument: str
    # Following fields are added to extend the model in order to make it compatible
    # with the OptionModel for backtesting
    tickersymbol: str = None
    last_price: float = 0
    profit: float = 0
    lot_size: int = 0
    backup_money: float = 0
    margin: HistoricalOptionMarginModel = DefaultVal(HistoricalOptionMarginModel)
    time_to_expiry_in_days: int = 0
    strike: float = 0
    # Enriched option related information
    percentage_dip: float = 0
    instrument_data: InstrumentModel = DefaultVal(InstrumentModel)
    sequence_id: int = 0
    profit_percentage: float = 0
    position: Optional[PositionModel] = DefaultVal(PositionModel)
    orders: Optional[List[OrderModel]] = DefaultVal(List[OrderModel])
    # TODO: Figure out a way to remove 'str' from the following, currently dataframe conversion transforms
    #       the underlying value to a stringified (not exactly) type which is not converatable back to an array
    instrument_positions:  Optional[Union[List[PositionModel], str]] = DefaultVal(List[PositionModel])
    enriched_instrument: EnrichedInstrumentModel = DefaultVal(EnrichedInstrumentModel)

    def __post_init__(self):
        self.tickersymbol = self.symbol
        self.tradingsymbol = self.symbol
        self.last_price = self.close

        if not OPTION_DATA_MAP.get(self.tickersymbol):
            raise ValueError('%s not configured for lot size in historical data' % self.tickersymbol)

        self.lot_size = OPTION_DATA_MAP[self.tickersymbol]['lot_size']
        self.backup_money = self.strike_price * self.lot_size
        self.margin = from_dict(
            data_class=HistoricalOptionMarginModel,
            data={ 'total': OPTION_DATA_MAP[self.tickersymbol]['margin_bckup_ratio'] * self.backup_money }
        )
        self.profit = self.last_price * self.lot_size
        self.time_to_expiry_in_days = (
            datetime.strptime(self.expiry, OPTIONS_EXPIRY_DATETIME_FORMAT) - datetime.now()
        ).days
        self.strike = self.strike_price
