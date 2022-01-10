from collections import defaultdict
from datetime import date
from typing import Dict, List

from src.apps.console.controllers.tradebook import DATETIME_FORMAT, TradebookController
from src.apps.console.models.tradebook import Trade, TRADE_TYPE_BUY, TRADE_TYPE_SELL
from src.apps.kite.controllers.holdings import HoldingsController
from src.utilities import calculate_cagr
from src.constants import TICKER_CHANGE_MAP
from src.logger import LOGGER


class CAGRController:
    @staticmethod
    def get_kite_cagr(from_date: date, to_date: date):
        trades = TradebookController.get_trades(segment='EQ', from_date=from_date, to_date=to_date)
        holdings = HoldingsController.get_holdings()

        temp_holdings_dict: Dict[str, List[Trade]] = defaultdict(list)
        sorted_trades: List[Trade] = sorted(trades, key=lambda x: x.trade_date)
        cagr_list = []

        for trade in sorted_trades:
            tradingsymbol = TICKER_CHANGE_MAP.get(trade.tradingsymbol, trade.tradingsymbol)

            if trade.trade_type == TRADE_TYPE_BUY:
                temp_holdings_dict[tradingsymbol].append(trade)

                continue
            elif trade.trade_type == TRADE_TYPE_SELL:
                if not temp_holdings_dict.get(tradingsymbol):
                    LOGGER.warn(
                        'Expected a existing bought holdings %s to exist for sell to happen, could not find' % trade.tradingsymbol
                    )

                    continue

                while trade.quantity > 0 and temp_holdings_dict[tradingsymbol]:
                    buy_trade: Trade = temp_holdings_dict[tradingsymbol][0]

                    cagr_list.append({
                        'cagr': '%.2f' % (calculate_cagr(
                            buy_date=buy_trade.trade_date_dt, buy_price=buy_trade.price,
                            sell_date=trade.trade_date_dt, sell_price=trade.price
                        ) * 100),
                        'tradingsymbol': tradingsymbol,
                        'buy_date': buy_trade.trade_date_dt.strftime(DATETIME_FORMAT),
                        'buy_price': buy_trade.price,
                        'sell_date': trade.trade_date_dt.strftime(DATETIME_FORMAT),
                        'sell_price': trade.price,
                        'quantity': trade.quantity,
                        'type': 'realized'
                    })

                    if trade.quantity > buy_trade.quantity:
                        temp_holdings_dict[tradingsymbol].pop(0)

                        trade.quantity -= buy_trade.quantity
                    else:
                        buy_trade.quantity -= trade.quantity
                        trade.quantity = 0

                if trade.quantity > 0:
                    raise Exception('Unable to match remaining sell quantity %d for %s to any buy quantity' % (trade.quantity, trade.tradingsymbol))
            else:
                raise ValueError('Unexpected trade type found: %s, should be one of [buy, sell]' % trade.trade_type)

        # TODO: Add unrealized profit/loss CAGR from holdings
        #       use temp_holdings as well to verify if any thing is remaining to be processed
        # TODO: Figure out how to calculate CAGR for money sitting idle
        # TODO: Figure out how to account for incoming money on a monthly basis

        columns = ['tradingsymbol', 'buy_date', 'buy_price', 'sell_date', 'sell_price', 'quantity', 'type', 'cagr']

        print(','.join(columns))

        for cagr_data in cagr_list:
            print(','.join([str(cagr_data[col]) for col in columns]))
