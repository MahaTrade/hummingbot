from decimal import Decimal
import logging
import pandas as pd
import numpy as np
from typing import (
    List,
    Dict,
    Optional
)
from math import (
    floor,
    ceil
)
import time
from hummingbot.core.clock cimport Clock
from hummingbot.core.event.events import TradeType, PriceType
from hummingbot.core.data_type.limit_order cimport LimitOrder
from hummingbot.core.data_type.limit_order import LimitOrder
from hummingbot.core.network_iterator import NetworkStatus
from hummingbot.connector.exchange_base import ExchangeBase
from hummingbot.connector.exchange_base cimport ExchangeBase
from hummingbot.core.event.events import OrderType

from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple
from hummingbot.strategy.strategy_base import StrategyBase
from hummingbot.client.config.global_config_map import global_config_map
from hummingbot.strategy.utils import order_age
from .data_types import (
    Proposal,
    PriceSize
)
from .spoofing_order_tracker cimport SpoofingOrderTracker


NaN = float("nan")
s_decimal_zero = Decimal(0)
s_decimal_neg_one = Decimal(-1)
pmm_logger = None


cdef class SpoofingStrategy(StrategyBase):
    OPTION_LOG_CREATE_ORDER = 1 << 3
    OPTION_LOG_MAKER_ORDER_FILLED = 1 << 4
    OPTION_LOG_STATUS_REPORT = 1 << 5
    OPTION_LOG_ALL = 0x7fffffffffffffff

    # These are exchanges where you're expected to expire orders instead of actively cancelling them.
    RADAR_RELAY_TYPE_EXCHANGES = {"radar_relay", "bamboo_relay"}

    @classmethod
    def logger(cls):
        global pmm_logger
        if pmm_logger is None:
            pmm_logger = logging.getLogger(__name__)
        return pmm_logger

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
        self._sb_order_tracker = SpoofingOrderTracker()
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

        self.c_add_markets([market_info.market])

    def all_markets_ready(self):
        return all([market.ready for market in self._sb_markets])

    @property
    def market_info(self) -> MarketTradingPairTuple:
        return self._market_info

    @property
    def order_amount(self) -> Decimal:
        return self._order_amount

    @order_amount.setter
    def order_amount(self, value: Decimal):
        self._order_amount = value

    @property
    def hanging_orders_enabled(self) -> bool:
        return self._hanging_orders_enabled

    @hanging_orders_enabled.setter
    def hanging_orders_enabled(self, value: bool):
        self._hanging_orders_enabled = value

    @property
    def hanging_orders_cancel_pct(self) -> Decimal:
        return self._hanging_orders_cancel_pct

    @hanging_orders_cancel_pct.setter
    def hanging_orders_cancel_pct(self, value: Decimal):
        self._hanging_orders_cancel_pct = value

    @property
    def bid_spread(self) -> Decimal:
        return self._bid_spread

    @bid_spread.setter
    def bid_spread(self, value: Decimal):
        self._bid_spread = value

    @property
    def order_refresh_time(self) -> float:
        return self._order_refresh_time

    @order_refresh_time.setter
    def order_refresh_time(self, value: float):
        self._order_refresh_time = value

    @property
    def trading_pair(self):
        return self._market_info.trading_pair

    @property
    def order_override(self):
        return self._order_override

    @order_override.setter
    def order_override(self, value: Dict[str, List[str]]):
        self._order_override = value

    def get_price(self) -> float:
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

    def get_last_price(self) -> float:
        return self._market_info.get_last_price()

    @property
    def hanging_order_ids(self) -> List[str]:
        return self._hanging_order_ids

    @property
    def market_info_to_active_orders(self) -> Dict[MarketTradingPairTuple, List[LimitOrder]]:
        return self._sb_order_tracker.market_pair_to_active_orders

    @property
    def active_orders(self) -> List[LimitOrder]:
        if self._market_info not in self.market_info_to_active_orders:
            return []
        return self.market_info_to_active_orders[self._market_info]

    @property
    def active_buys(self) -> List[LimitOrder]:
        return [o for o in self.active_orders if o.is_buy]

    @property
    def active_non_hanging_orders(self) -> List[LimitOrder]:
        orders = [o for o in self.active_orders if o.client_order_id not in self._hanging_order_ids]
        return orders

    @property
    def logging_options(self) -> int:
        return self._logging_options

    @logging_options.setter
    def logging_options(self, int64_t logging_options):
        self._logging_options = logging_options

    # The following exposed Python functions are meant for unit tests
    # ---------------------------------------------------------------
    def execute_orders_proposal(self, proposal: Proposal):
        return self.c_execute_orders_proposal(proposal)

    def cancel_order(self, order_id: str):
        return self.c_cancel_order(self._market_info, order_id)

    # ---------------------------------------------------------------

    cdef c_start(self, Clock clock, double timestamp):
        StrategyBase.c_start(self, clock, timestamp)
        self._last_timestamp = timestamp
        # start tracking any restored limit order
        restored_order_ids = self.c_track_restored_orders(self.market_info)
        # make restored order hanging orders
        for order_id in restored_order_ids:
            self._hanging_order_ids.append(order_id)

    cdef c_tick(self, double timestamp):
        StrategyBase.c_tick(self, timestamp)
        cdef:
            int64_t current_tick = <int64_t > (timestamp // self._status_report_interval)
            int64_t last_tick = <int64_t > (self._last_timestamp // self._status_report_interval)
            bint should_report_warnings = ((current_tick > last_tick) and
                                           (self._logging_options & self.OPTION_LOG_STATUS_REPORT))
            cdef object proposal
        try:
            if not self._all_markets_ready:
                self._all_markets_ready = all([market.ready for market in self._sb_markets])
                if not self._all_markets_ready:
                    # Markets not ready yet. Don't do anything.
                    if should_report_warnings:
                        self.logger().warning(f"Markets are not ready. No market making trades are permitted.")
                    return

            if should_report_warnings:
                if not all([market.network_status is NetworkStatus.CONNECTED for market in self._sb_markets]):
                    self.logger().warning(f"WARNING: Some markets are not connected or are down at the moment. Market "
                                          f"making may be dangerous when markets or networks are unstable.")

            proposal = None
            asset_mid_price = Decimal("0")
            # asset_mid_price = self.c_set_mid_price(market_info)
            if self._create_timestamp <= self._current_timestamp:
                # 1. Create base order proposals
                proposal = self.c_create_base_proposal()

            self.c_cancel_active_orders_on_max_age_limit()
            self.c_cancel_active_orders(proposal)
            self.c_cancel_hanging_orders()
            self.c_cancel_orders_above_max_spread()
            if self.c_to_create_orders(proposal):
                self.c_execute_orders_proposal(proposal)
        finally:
            self._last_timestamp = timestamp

    cdef object c_create_base_proposal(self):
        cdef:
            ExchangeBase market = self._market_info.market
            list buys = []

        buy_reference_price = self.get_price()

        # First to check if a customized order override is configured, otherwise the proposal will be created according
        # to order spread, amount, and levels setting.
        order_override = self._order_override
        if order_override is not None and len(order_override) > 0:
            for key, value in order_override.items():
                if str(value[0]) in ["buy"]:
                    price = buy_reference_price * (Decimal("1") - Decimal(str(value[1])) / Decimal("100"))
                    price = market.c_quantize_order_price(self.trading_pair, price)
                    size = Decimal(str(value[2]))
                    size = market.c_quantize_order_amount(self.trading_pair, size)
                    if size > 0 and price > 0:
                        buys.append(PriceSize(price, size))
        else:
            price = buy_reference_price * (Decimal("1") - self._bid_spread)
            price = market.c_quantize_order_price(self.trading_pair, price)
            size = self._order_amount
            size = market.c_quantize_order_amount(self.trading_pair, size)
            if size > 0:
                buys.append(PriceSize(price, size))
        return Proposal(buys)

    cdef c_cancel_active_orders_on_max_age_limit(self):
        """
        Cancels active non hanging orders if they are older than max age limit
        """
        cdef:
            list active_orders = self.active_non_hanging_orders
        if active_orders and any(order_age(o) > self._max_order_age for o in active_orders):
            for order in active_orders:
                self.c_cancel_order(self._market_info, order.client_order_id)

    cdef c_cancel_active_orders(self, object proposal):
        """
        Cancels active non hanging orders, checks if the order prices are within tolerance threshold
        """
        if self._cancel_timestamp > self._current_timestamp:
            return
        if not global_config_map.get("0x_active_cancels").value:
            if ((self._market_info.market.name in self.RADAR_RELAY_TYPE_EXCHANGES) or
                    (self._market_info.market.name == "bamboo_relay" and not self._market_info.market.use_coordinator)):
                return

        cdef:
            list active_orders = self.active_non_hanging_orders
            list active_buy_prices = []
            bint to_defer_canceling = False
        if len(active_orders) == 0:
            return

        if not to_defer_canceling:
            for order in active_orders:
                self.c_cancel_order(self._market_info, order.client_order_id)
        # else:
        #     self.set_timers()

    cdef c_cancel_hanging_orders(self):
        if not global_config_map.get("0x_active_cancels").value:
            if ((self._market_info.market.name in self.RADAR_RELAY_TYPE_EXCHANGES) or
                    (self._market_info.market.name == "bamboo_relay" and not self._market_info.market.use_coordinator)):
                return

        cdef:
            object price = self.get_price()
            list active_orders = self.active_orders
            list orders
            LimitOrder order
        for h_order_id in self._hanging_order_ids:
            orders = [o for o in active_orders if o.client_order_id == h_order_id]
            if orders and price > 0:
                order = orders[0]
                if abs(order.price - price) / price >= self._hanging_orders_cancel_pct:
                    self.c_cancel_order(self._market_info, order.client_order_id)
                # hanging orders older than max age are canceled and marked to be recreated.
                elif order_age(order) > self._max_order_age:
                    self.c_cancel_order(self._market_info, order.client_order_id)
                    self._hanging_order_ids.remove(order.client_order_id)
                    self._hanging_orders_to_recreate.append(order)

    cdef c_did_cancel_order(self, object cancelled_event):
        cdef:
            list orders = [o for o in self._hanging_orders_to_recreate if o.client_order_id == cancelled_event.order_id]
        if orders:
            self.c_recreate_hanging_order(orders[0])

    @property
    def hanging_orders_to_recreate(self) -> List[LimitOrder]:
        return self._hanging_orders_to_recreate

    cdef c_recreate_hanging_order(self, object order):
        """
        To recreate hanging orders which are older than max order age limit
        :param order: The hanging order to be recreated.
        """
        cdef:
            str order_id
            LimitOrder hanging_order = order
        if self._logging_options:
            self.logger().info(f"Recreating hanging order: {hanging_order.client_order_id} ")
        if order.is_buy:
            order_id = self.c_buy_with_specific_market(
                self._market_info,
                hanging_order.quantity,
                order_type=self._limit_order_type,
                price=hanging_order.price
            )
        self.logger().info(f"New hanging order: {order_id} ")
        self._hanging_orders_to_recreate.remove(order)
        self._hanging_order_ids.append(order_id)

    # Cancel Non-Hanging, Active Orders if Spreads are above maximum_spread
    cdef c_cancel_orders_above_max_spread(self):
        cdef:
            list active_orders = self.market_info_to_active_orders.get(self._market_info, [])
            object price = self.get_price()
        active_orders = [order for order in active_orders
                         if order.client_order_id not in self._hanging_order_ids]
        for order in active_orders:
            negation = -1 if order.is_buy else 1
            print(1001, negation, order.price, price, (negation * (order.price - price) / price), self._maximum_spread)
            if (negation * (order.price - price) / price) > self._maximum_spread:
                self.logger().info(f"Order is above maximum spread ({self._maximum_spread})."
                                   f" Cancelling Order: ({'Buy' if order.is_buy else 'Sell'}) "
                                   f"ID - {order.client_order_id}")
                self.c_cancel_order(self._market_info, order.client_order_id)
            print('1006', abs(order.price - price) / price, '>=', self._hanging_orders_cancel_pct)
            if abs(order.price - price) / price >= self._hanging_orders_cancel_pct:
                self.c_cancel_order(self._market_info, order.client_order_id)

    cdef bint c_to_create_orders(self, object proposal):
        return self._create_timestamp < self._current_timestamp and \
            proposal is not None and \
            len(self.active_non_hanging_orders) == 0

    cdef c_execute_orders_proposal(self, object proposal):
        cdef:
            double expiration_seconds = (self._order_refresh_time
                                         if ((self._market_info.market.name in self.RADAR_RELAY_TYPE_EXCHANGES) or
                                             (self._market_info.market.name == "bamboo_relay" and
                                              not self._market_info.market.use_coordinator))
                                         else NaN)
            str bid_order_id
            bint orders_created = False

        if len(proposal.buys) > 0:
            # if self._logging_options & self.OPTION_LOG_CREATE_ORDER:
            # price_quote_str = [f"{buy.size.normalize()} {self.base_asset}, "
            #                   f"{buy.price.normalize()} {self.quote_asset}"
            #                   for buy in proposal.buys]
            # self.logger().info(
            #   f"({self.trading_pair}) Creating {len(proposal.buys)} bid orders "
            #    f"at (Size, Price): {price_quote_str}"
            # )
            for buy in proposal.buys:
                bid_order_id = self.c_buy_with_specific_market(
                    self._market_info,
                    buy.size,
                    order_type=self._limit_order_type,
                    price=buy.price,
                    expiration_seconds=expiration_seconds
                )
                orders_created = True
        if orders_created:
            self.set_timers()

    cdef set_timers(self):
        cdef double next_cycle = self._current_timestamp + self._order_refresh_time
        if self._create_timestamp <= self._current_timestamp:
            self._create_timestamp = next_cycle
        if self._cancel_timestamp <= self._current_timestamp:
            self._cancel_timestamp = min(self._create_timestamp, next_cycle)

    def notify_hb_app(self, msg: str):
        if self._hb_app_notification:
            super().notify_hb_app(msg)

    def get_price_type(self, price_type_str: str) -> PriceType:
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
