from .uniswap_stable_price import UniswapStablePrice
from .uniswap_stable_price_config_map import uniswap_stable_price_config_map as c_map


def start(self):
    rpc_url = c_map.get("rpc_url").value.lower()

    seller_contract_address = c_map.get('seller_contract_address').value.lower()
    min_profit = c_map.get('min_profit').value
    target_price = c_map.get('target_price').value
    token0_address = c_map.get('token0_address').value.lower()
    token1_address = c_map.get('token1_address').value.lower()
    pair_address = c_map.get('pair_address').value.lower()
    router_address = c_map.get('router_address').value.lower()

    # self._initialize_markets([(connector, [market])])
    # base, quote = market.split("-")
    # market_info = MarketTradingPairTuple(self.markets[connector], market, base, quote)
    # self.market_trading_pair_tuples = [market_info]

    self.strategy = UniswapStablePrice(
        rpc_url=rpc_url,
        seller_contract_address=seller_contract_address,
        min_profit=min_profit,
        target_price=target_price,
        token0_address=token0_address,
        token1_address=token1_address,
        pair_address=pair_address,
        router_address=router_address,
    )
    # self.strategy = LimitOrder(market_info)
