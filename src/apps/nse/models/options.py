from dataclasses import dataclass, field
from datetime import datetime
from src.apps.kite.models.orders import OrderModel
from src.apps.kite.models.positions import PositionModel
from src.apps.kite.models.instruments import EnrichedInstrumentModel, InstrumentModel
from src.constants import OPTION_DATA_MAP
from typing import Any, List, Optional, Union

from dacite.core import from_dict

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
    oi: float = 0
    backup_money: float = 0
    margin: Optional[HistoricalOptionMarginModel] = field(default=None)
    time_to_expiry_in_days: int = 0
    strike: float = 0
    # Enriched option related information
    percentage_dip: float = 0
    instrument_data: Optional[InstrumentModel] = field(default=None)
    sequence_id: int = 0
    profit_percentage: float = 0
    position: Optional[PositionModel] = field(default=None)
    orders: Optional[List[OrderModel]] = field(default_factory=list)
    # TODO: Figure out a way to remove 'str' from the following, currently dataframe conversion transforms
    #       the underlying value to a stringified (not exactly) type which is not converatable back to an array
    instrument_positions:  Optional[Union[List[PositionModel], str]] = field(default_factory=list)
    enriched_instrument: Optional[EnrichedInstrumentModel] = field(default=None)

    def __post_init__(self):
        self.tickersymbol = self.symbol
        self.tradingsymbol = self.symbol
        self.last_price = self.close
        self.oi = self.open_int

        if not OPTION_DATA_MAP.get(self.tickersymbol):
            raise ValueError('%s not configured for lot size in historical data' % self.tickersymbol)

        self.lot_size = OPTION_DATA_MAP[self.tickersymbol].lot_size
        self.backup_money = self.strike_price * self.lot_size
        self.margin = from_dict(
            data_class=HistoricalOptionMarginModel,
            data={ 'total': OPTION_DATA_MAP[self.tickersymbol].margin_backup_ratio * self.backup_money }
        )
        self.profit = self.last_price * self.lot_size
        self.time_to_expiry_in_days = (
            datetime.strptime(self.expiry, OPTIONS_EXPIRY_DATETIME_FORMAT) - datetime.now()
        ).days
        self.strike = self.strike_price
