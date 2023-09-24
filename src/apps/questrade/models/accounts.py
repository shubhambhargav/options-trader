from dataclasses import dataclass
from typing import Optional


@dataclass
class AccountBalanceModel:
    currency: str
    cash: float
    marketValue: float
    totalEquity: float
    buyingPower: float
    maintenanceExcess: float

@dataclass
class PositionModel:
    symbol: str
    symbolId: int
    openQuantity: float
    closedQuantity: float
    currentPrice: float
    averageEntryPrice: float
    closedPnL: Optional[float]
    openPnL: Optional[float]
    totalCost: Optional[float]

@dataclass
class OrderModel:
    id: int
    symbol: str
    symbolId: str
    totalQuantity: int
    openQuantity: int
    filledQuantity: int
    canceledQuantity: int
    orderType: str
