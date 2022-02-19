#!/usr/bin/env python

import logging
from hummingbot.logger import HummingbotLogger
from hummingbot.strategy.strategy_py_base import StrategyPyBase

from web3 import Web3

hws_logger = None


class UniswapStablePrice(StrategyPyBase):
    @classmethod
    def logger(cls) -> HummingbotLogger:
        global hws_logger
        if hws_logger is None:
            hws_logger = logging.getLogger(__name__)
        return hws_logger

    def __init__(
        self,
        rpc_url: str,
        seller_contract_address: str,
        min_profit: int,
        target_price: int,
        token0_address: str,
        token1_address: str,
        pair_address: str,
        router_address: str
    ):
        super().__init__()
        self.rpc_url = rpc_url
        self.seller_contract_address = seller_contract_address
        self.min_profit = min_profit
        self.target_price = target_price
        self.token0_address = token0_address
        self.token1_address = token1_address
        self.pair_address = pair_address
        self.router_address = router_address

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        print(self.w3.eth.chain_id)

    # After initializing the required variables, we define the tick method.
    # The tick method is the entry point for the strategy.
    def tick(self, timestamp: float):
        self.logger().info("testing" + str(timestamp))

        # if not self._connector_ready:
        #     self._connector_ready = self._market_info.market.ready
        #     if not self._connector_ready:
        #         self.logger().warning(f"{self._market_info.market.name} is not ready. Please wait...")
        #         return
        #     else:
        #         self.logger().warning(f"{self._market_info.market.name} is ready. Trading started")

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

    # # Emit a log message when the order completes
    # def did_complete_buy_order(self, order_completed_event):
    #     self.logger().info(f"Your limit buy order {order_completed_event.order_id} has been executed")
    #     self.logger().info(order_completed_event)
