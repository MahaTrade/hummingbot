from typing import (
    List,
    Tuple,
)

from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple
from hummingbot.strategy.spoofing_new import SpoofingStrategy
from hummingbot.strategy.spoofing_new.spoofing_new_config_map import spoofing_new_config_map as c_map
from decimal import Decimal


def start(self):
    try:
        order_amount = c_map.get("order_amount").value
        order_refresh_time = c_map.get("order_refresh_time").value
        max_order_age = c_map.get("max_order_age").value
        bid_spread = c_map.get("bid_spread").value / Decimal('100')
        maximum_spread = c_map.get("maximum_spread").value / Decimal('100')
        exchange = c_map.get("exchange").value.lower()
        raw_trading_pair = c_map.get("market").value
        hanging_orders_cancel_pct = c_map.get("hanging_orders_cancel_pct").value / Decimal('100')
        price_type = c_map.get("price_type").value
        order_override = c_map.get("order_override").value
        base, quote = raw_trading_pair.split("-")
        trading_pair: str = raw_trading_pair
        maker_assets: Tuple[str, str] = self._initialize_market_assets(exchange, [trading_pair])[0]
        market_names: List[Tuple[str, List[str]]] = [(exchange, [trading_pair])]
        self._initialize_wallet(token_trading_pairs=list(set(maker_assets)))
        self._initialize_markets(market_names)
        self.assets = set(maker_assets)
        maker_data = [self.markets[exchange], trading_pair] + list(maker_assets)
        self.market_trading_pair_tuples = [MarketTradingPairTuple(*maker_data)]

        strategy_logging_options = SpoofingStrategy.OPTION_LOG_ALL

        self.strategy = SpoofingStrategy(
            market_info=MarketTradingPairTuple(*maker_data),
            bid_spread=bid_spread,
            order_amount=order_amount,
            order_refresh_time=order_refresh_time,
            max_order_age = max_order_age,
            hanging_orders_cancel_pct=hanging_orders_cancel_pct,
            logging_options=strategy_logging_options,
            price_type=price_type,
            maximum_spread=maximum_spread,
            hb_app_notification=True,
            order_override={} if order_override is None else order_override,
        )
    except Exception as e:
        self._notify(str(e))
        self.logger().error("Unknown error during initialization.", exc_info=True)
