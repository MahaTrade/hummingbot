from web3 import Web3
import json
import pathlib
from hummingbot.strategy.strategy_py_base import StrategyPyBase


class Web3Strategy(StrategyPyBase):
    def __init__(self,
                 infura_url,
                 contract_address
                 ):

        super().__init__()
        self._infura_url = infura_url
        self._contract_address = contract_address

    def tick(self, timestamp: float):
        web3 = Web3(Web3.HTTPProvider(self._infura_url))
        path = pathlib.Path(__file__).parent.resolve()
        file = f'{path}/abi/test_contract.json'
        print(file)
        with open(file) as f:
            abi = json.load(f)

        contract = web3.eth.contract(address=self._contract_address, abi=abi)

        print(contract.functions.balanceOf('0x5Ce3bB14DD7aE28fa059384C12c8A26877B91192').call())
