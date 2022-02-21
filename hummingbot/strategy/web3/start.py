from hummingbot.strategy.web3.web3_config_map import web3_config_map as c_map
from .web3_strategy import Web3Strategy


def start(self):
    infura_url = c_map.get("infura_url").value.lower()
    contract_address = c_map.get("contract_address").value

    self.strategy = Web3Strategy(
        infura_url,
        contract_address
    )
