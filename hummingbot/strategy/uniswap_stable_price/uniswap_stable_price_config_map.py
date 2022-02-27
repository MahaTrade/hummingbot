from hummingbot.client.config.config_var import ConfigVar
from hummingbot.client.config.config_validators import (validate_decimal)

# List of parameters defined by the strategy
uniswap_stable_price_config_map = {
    "strategy": ConfigVar(
        key="strategy",
        prompt="",
        default="uniswap_stable_price",
    ),

    "rpc_url": ConfigVar(
        key="rpc_url",
        prompt="Enter the RPC http url to connect to >>> ",
        prompt_on_new=True,
        default=False,
    ),

    "rpc_ws_url": ConfigVar(
        key="rpc_ws_url",
        prompt="Enter the RPC websocket url to connect to >>> ",
        prompt_on_new=True,
        default=False,
    ),

    "seller_contract_address": ConfigVar(
        key="seller_contract_address",
        prompt="Enter the seller contract address",
        default=False
    ),

    "min_profit": ConfigVar(
        key="min_profit",
        prompt="min profit?",
        default="500",
        type_str="decimal",
        validator=validate_decimal
    ),

    "target_price": ConfigVar(
        key="target_price",
        type_str="decimal",
        prompt="Target price?",
        validator=validate_decimal,
        default=False,
    ),

    "token0_address": ConfigVar(
        prompt="Enter the adddress of the ARTH token to trade >>> ",
        prompt_on_new=True,
        key="token0_address",
        default=False,
    ),

    "token0_decimals": ConfigVar(
        default=18,
        key="token0_decimals",
        prompt_on_new=True,
        prompt="Enter the decimals of the ARTH token to trade >>> ",
        type_str="decimal",
    ),

    "token1_decimals": ConfigVar(
        default=18,
        key="token1_decimals",
        prompt_on_new=True,
        prompt="Enter the decimals of the second token to trade >>> ",
        type_str="decimal",
    ),

    "token0_symbol": ConfigVar(
        default="ARTH",
        key="token0_symbol",
        prompt_on_new=True,
        prompt="Enter the symbol of the ARTH token to trade >>> ",
    ),

    "token1_symbol": ConfigVar(
        default="BUSD",
        key="token1_symbol",
        prompt_on_new=True,
        prompt="Enter the symbol of the second token to trade >>> ",
    ),

    "token1_address": ConfigVar(
        prompt="Enter the adddress of the second token to trade >>> ",
        key="token1_address",
        default=False,
    ),

    "pair_address": ConfigVar(
        key="connector",
        prompt="Enter the name of the pair to trade >>> ",
        prompt_on_new=True,
    ),

    "router_address": ConfigVar(
        key="connector",
        prompt="Enter the name of the router >>> ",
        prompt_on_new=True,
    )
}
