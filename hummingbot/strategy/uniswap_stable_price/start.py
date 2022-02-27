from .uniswap_stable_price import UniswapStablePrice
from .uniswap_stable_price_config_map import uniswap_stable_price_config_map as c_map
from hummingbot.client.config.global_config_map import global_config_map


def start(self):
    rpc_url = c_map.get("rpc_url").value.lower()

    seller_contract_address = c_map.get('seller_contract_address').value.lower()
    min_profit = c_map.get('min_profit').value
    target_price = c_map.get('target_price').value
    token0_address = c_map.get('token0_address').value.lower()
    token1_address = c_map.get('token1_address').value.lower()
    pair_address = c_map.get('pair_address').value.lower()
    router_address = c_map.get('router_address').value.lower()
    token0_decimals = c_map.get('token0_decimals').value
    explorer_url = c_map.get('explorer_url').value
    token1_decimals = c_map.get('token1_decimals').value
    token0_symbol = c_map.get('token0_symbol').value
    token1_symbol = c_map.get('token1_symbol').value
    rpc_ws_url = c_map.get('rpc_ws_url').value.lower()
    ethereum_wallet = global_config_map.get("ethereum_wallet").value

    self.strategy = UniswapStablePrice(
        explorer_url=explorer_url,
        ethereum_wallet=ethereum_wallet,
        token0_decimals=token0_decimals,
        token1_decimals=token1_decimals,
        token0_symbol=token0_symbol,
        token1_symbol=token1_symbol,
        rpc_ws_url=rpc_ws_url,
        rpc_url=rpc_url,
        seller_contract_address=seller_contract_address,
        min_profit=min_profit,
        target_price=target_price,
        token0_address=token0_address,
        token1_address=token1_address,
        pair_address=pair_address,
        router_address=router_address,
    )
