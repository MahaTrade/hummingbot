#!/usr/bin/env python

from decimal import Decimal
import logging
from typing import (
    List,
    Dict
)
from hummingbot.core.event.events import PriceType
from hummingbot.core.event.events import OrderType
# from hummingbot.core.data_type.limit_order import LimitOrder
from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple
from hummingbot.logger import HummingbotLogger
from .data_types import (
    Proposal
)
from hummingbot.strategy.strategy_py_base import StrategyPyBase
# from hummingbot.strategy.strategy_base import StrategyBase

hws_logger = None


class SpoofingStrategy(StrategyPyBase):
    # We use StrategyPyBase to inherit the structure. We also
    # create a logger object before adding a constructor to the class.

    OPTION_LOG_CREATE_ORDER = 1 << 3
    OPTION_LOG_MAKER_ORDER_FILLED = 1 << 4
    OPTION_LOG_STATUS_REPORT = 1 << 5
    OPTION_LOG_ALL = 0x7fffffffffffffff

    @classmethod
    def logger(cls) -> HummingbotLogger:
        global hws_logger
        if hws_logger is None:
            hws_logger = logging.getLogger(__name__)
        return hws_logger

    def __init__(self,
                 market_info: MarketTradingPairTuple,
                 bid_spread: Decimal,
                 order_amount: Decimal,
                 order_refresh_time: float = 30.0,
                 max_order_age = 1800.0,
                 hanging_orders_cancel_pct: Decimal = Decimal("0.1"),
                 logging_options: int = OPTION_LOG_ALL,
                 price_type: str = "mid_price",
                 status_report_interval: float = 900,
                 maximum_spread: Decimal = Decimal(0),
                 hb_app_notification: bool = False,
                 order_override: Dict[str, List[str]] = {},
                 ):

        super().__init__()
        # self._sb_order_tracker = SpoofingOrderTracker()
        self._connector_ready = False
        self._market_info = market_info
        self._bid_spread = bid_spread
        self._maximum_spread = maximum_spread
        self._order_amount = order_amount
        self._order_refresh_time = order_refresh_time
        self._max_order_age = max_order_age
        self._hanging_orders_cancel_pct = hanging_orders_cancel_pct
        self._price_type = self.get_price_type(price_type)
        self._hb_app_notification = hb_app_notification
        self._order_override = order_override
        self.active_order = ''
        self._cancel_timestamp = 0
        self._create_timestamp = 0
        self._hanging_orders_to_recreate = []
        self._limit_order_type = self._market_info.market.get_maker_order_type()
        self._all_markets_ready = False
        self._filled_buys_balance = 0
        self._hanging_order_ids = []
        self._logging_options = logging_options
        self._last_timestamp = 0
        self._status_report_interval = status_report_interval
        self._last_own_trade_price = Decimal('nan')
        self._connector_ready = False
        self._order_completed = False
        self.add_markets([market_info.market])

    # After initializing the required variables, we define the tick method.
    # The tick method is the entry point for the strategy.

    def execute_orders_proposal(self, proposal: Proposal):
        return self.c_execute_orders_proposal(proposal)

    def cancel_order(self, order_id: str):
        return self.c_cancel_order(self._market_info, order_id)

    def get_price(self):
        price_provider = self._market_info
        if self._price_type is PriceType.LastOwnTrade:
            price = self._last_own_trade_price
        elif self._price_type is PriceType.InventoryCost:
            price = price_provider.get_price_by_type(PriceType.MidPrice)
        else:
            price = price_provider.get_price_by_type(self._price_type)

        if price.is_nan():
            price = price_provider.get_price_by_type(PriceType.MidPrice)

        return price

    def active_non_hanging_orders(self):
        orders = [o for o in self.active_orders]
        return orders

    def tick(self, timestamp: float):
        if not self._connector_ready:
            self._connector_ready = self._market_info.market.ready
            if not self._connector_ready:
                self.logger().warning(f"{self._market_info.market.name} is not ready. Please wait...")
                return
            else:
                self.logger().warning(f"{self._market_info.market.name} is ready. Trading started")
        # proposal = None

        # proposal = self.create_base_proposal()

        # print('proposal', proposal)

        self.create_buy()
        # self.cancel_active_order()

        # if not self._order_completed:
        #     # The get_mid_price method gets the mid price of the coin and
        #     # stores it. This method is derived from the MarketTradingPairTuple class.
        #     mid_price = self._market_info.get_mid_price()

        #     # The buy_with_specific_market method executes the trade for you. This
        #     # method is derived from the Strategy_base class.
        #     order_id = self.buy_with_specific_market(
        #         self._market_info,  # market_trading_pair_tuple
        #         Decimal("0.5"),   # amount
        #         OrderType.LIMIT,    # order_type
        #         mid_price           # price
        #     )
        #     self.logger().info(f"Submitted limit buy order {order_id}")
        #     self._order_completed = True

    # Emit a log message when the order completes
    # def did_complete_buy_order(self, order_completed_event):
    #     self.logger().info(f"Your limit buy order {order_completed_event.order_id} has been executed")
    #     self.logger().info(order_completed_event)

    # def create_base_proposal(self):
    #     market = self._market_info.market
    #     buys = []

    #     buy_reference_price = self.get_price()

    #     # First to check if a customized order override is configured, otherwise the proposal will be created according
    #     # to order spread, amount, and levels setting.
    #     order_override = self._order_override
    #     if order_override is not None and len(order_override) > 0:
    #         for key, value in order_override.items():
    #             if str(value[0]) in ["buy"]:
    #                 price = buy_reference_price * (Decimal("1") - Decimal(str(value[1])) / Decimal("100"))
    #                 price = market.c_quantize_order_price(self.trading_pair, price)
    #                 size = Decimal(str(value[2]))
    #                 size = market.c_quantize_order_amount(self.trading_pair, size)
    #                 if size > 0 and price > 0:
    #                     buys.append(PriceSize(price, size))
    #     else:
    #         price = buy_reference_price * (Decimal("1") - self._bid_spread)
    #         price = market.c_quantize_order_price(self.trading_pair, price)
    #         size = self._order_amount
    #         size = market.c_quantize_order_amount(self.trading_pair, size)
    #         if size > 0:
    #             buys.append(PriceSize(price, size))
    #     return Proposal(buys)

    def create_buy(self):
        # mid_price = self._market_info.get_mid_price()
        buy_reference_price = self.get_price()
        price = buy_reference_price * (Decimal("1") - self._bid_spread)
        amount = self._order_amount
        if not self._order_completed:
            order_id = self.buy_with_specific_market(
                self._market_info,  # market_trading_pair_tuple
                amount,   # amount
                OrderType.LIMIT,    # order_type
                price           # price
            )
            self.active_order = order_id
            print(self.active_order)
            self.logger().info(f"Submitted limit buy order {order_id}")
            self._order_completed = True

    def cancel_active_order(self):
        print('active_orders', self.active_order)
        self.cancel_order(self._market_info, self.active_order)

    def get_price_type(self, price_type_str: str):
        print('>>>>>>>>>>>>>>>>>>>>>>price_type_str', price_type_str)
        if price_type_str == "mid_price":
            return PriceType.MidPrice
        elif price_type_str == "best_bid":
            return PriceType.BestBid
        elif price_type_str == "last_price":
            return PriceType.LastTrade
        elif price_type_str == 'last_own_trade_price':
            return PriceType.LastOwnTrade
        elif price_type_str == 'inventory_cost':
            return PriceType.InventoryCost
        else:
            raise ValueError(f"Unrecognized price type string {price_type_str}.")
