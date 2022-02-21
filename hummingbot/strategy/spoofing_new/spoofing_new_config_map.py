from decimal import Decimal

from hummingbot.client.config.config_var import ConfigVar
from hummingbot.client.config.config_validators import (
    validate_exchange,
    validate_market_trading_pair,
    validate_decimal,
)
from hummingbot.client.settings import (
    required_exchanges,
    EXAMPLE_PAIRS,
)
from hummingbot.client.config.global_config_map import (
    using_bamboo_coordinator_mode,
    using_exchange
)
from hummingbot.client.config.config_helpers import (
    minimum_order_amount,
)
from typing import Optional


def maker_trading_pair_prompt():
    exchange = spoofing_new_config_map.get("exchange").value
    example = EXAMPLE_PAIRS.get(exchange)
    return "Enter the token trading pair you would like to trade on %s%s >>> " \
           % (exchange, f" (e.g. {example})" if example else "")


# strategy specific validators
def validate_exchange_trading_pair(value: str) -> Optional[str]:
    exchange = spoofing_new_config_map.get("exchange").value
    return validate_market_trading_pair(exchange, value)


async def order_amount_prompt() -> str:
    exchange = spoofing_new_config_map["exchange"].value
    trading_pair = spoofing_new_config_map["market"].value
    base_asset, quote_asset = trading_pair.split("-")
    min_amount = await minimum_order_amount(exchange, trading_pair)
    return f"What is the amount of {base_asset} per order? (minimum {min_amount}) >>> "


async def validate_order_amount(value: str) -> Optional[str]:
    try:
        exchange = spoofing_new_config_map["exchange"].value
        trading_pair = spoofing_new_config_map["market"].value
        min_amount = await minimum_order_amount(exchange, trading_pair)
        if Decimal(value) < min_amount:
            return f"Order amount must be at least {min_amount}."
    except Exception:
        return "Invalid order amount."


def exchange_on_validated(value: str):
    required_exchanges.append(value)


spoofing_new_config_map = {
    "strategy":
        ConfigVar(key="strategy",
                  prompt=None,
                  default="spoofing_new"),
    "exchange":
        ConfigVar(key="exchange",
                  prompt="Enter your maker spot connector >>> ",
                  validator=validate_exchange,
                  on_validated=exchange_on_validated,
                  prompt_on_new=True),
    "market":
        ConfigVar(key="market",
                  prompt=maker_trading_pair_prompt,
                  validator=validate_exchange_trading_pair,
                  prompt_on_new=True),
    "bid_spread":
        ConfigVar(key="bid_spread",
                  prompt="How far away from the mid price do you want to place the "
                         "first bid order? (Enter 1 to indicate 1%) >>> ",
                  type_str="decimal",
                  validator=lambda v: validate_decimal(v, 0, 100, inclusive=False),
                  prompt_on_new=True),
    "maximum_spread":
        ConfigVar(key="maximum_spread",
                  prompt="At what minimum spread should the bot automatically cancel orders? (Enter 1 for 1%) >>> ",
                  type_str="decimal",
                  validator=lambda v: validate_decimal(v, 0, 100, True),
                  prompt_on_new=True),
    "order_refresh_time":
        ConfigVar(key="order_refresh_time",
                  prompt="How often do you want to cancel and replace bids and asks "
                         "(in seconds)? >>> ",
                  required_if=lambda: not (using_exchange("radar_relay")() or
                                           (using_exchange("bamboo_relay")() and not using_bamboo_coordinator_mode())),
                  type_str="float",
                  validator=lambda v: validate_decimal(v, 0, inclusive=False),
                  prompt_on_new=True),
    "max_order_age":
        ConfigVar(key="max_order_age",
                  prompt="How long do you want to cancel and replace bids and asks "
                         "with the same price (in seconds)? >>> ",
                  required_if=lambda: not (using_exchange("radar_relay")() or
                                           (using_exchange("bamboo_relay")() and not using_bamboo_coordinator_mode())),
                  type_str="float",
                  default=Decimal("1800"),
                  validator=lambda v: validate_decimal(v, 0, inclusive=False)),
    "order_amount":
        ConfigVar(key="order_amount",
                  prompt=order_amount_prompt,
                  type_str="decimal",
                  validator=validate_order_amount,
                  prompt_on_new=True),
    "hanging_orders_cancel_pct":
        ConfigVar(key="hanging_orders_cancel_pct",
                  prompt="At what spread percentage (from mid price) will hanging orders be canceled? "
                         "(Enter 1 to indicate 1%) >>> ",
                  type_str="decimal",
                  default=Decimal("10"),
                  validator=lambda v: validate_decimal(v, 0, 100, inclusive=False)),
    "order_override":
        ConfigVar(key="order_override",
                  prompt=None,
                  required_if=lambda: False,
                  default=None,
                  type_str="json"),
    "price_type":
        ConfigVar(key="price_type",
                  prompt="Which price type to use? ("
                         "mid_price/last_price/last_own_trade_price/best_bid/best_ask/inventory_cost) >>> ",
                  type_str="str",
                  default="mid_price",
                  validator=lambda s: None if s in {"mid_price",
                                                    "last_price",
                                                    "last_own_trade_price",
                                                    "best_bid",
                                                    "best_ask",
                                                    "inventory_cost",
                                                    } else
                  "Invalid price type."),
}
