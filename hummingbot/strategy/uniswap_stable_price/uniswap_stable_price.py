#!/usr/bin/env python

import logging
from hummingbot.logger import HummingbotLogger
from hummingbot.strategy.strategy_py_base import StrategyPyBase

import json
import pathlib
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
        ethereum_wallet: str,
        rpc_ws_url: str,
        rpc_url: str,
        seller_contract_address: str,
        min_profit: int,
        target_price: int,
        token0_decimals: str,
        token1_decimals: str,
        token0_symbol: str,
        token1_symbol: str,
        token0_address: str,
        token1_address: str,
        pair_address: str,
        router_address: str
    ):
        super().__init__()

        self.ethereum_wallet = ethereum_wallet
        self.rpc_ws_url = rpc_ws_url
        self.rpc_url = rpc_url
        self.seller_contract_address = Web3.toChecksumAddress(seller_contract_address)
        self.min_profit = min_profit
        self.target_price = target_price
        self.token0_address = Web3.toChecksumAddress(token0_address)
        self.token1_address = Web3.toChecksumAddress(token1_address)
        self.pair_address = Web3.toChecksumAddress(pair_address)
        self.router_address = Web3.toChecksumAddress(router_address)

        self.token0_decimals = token0_decimals
        self.token1_decimals = token1_decimals
        self.token0_symbol = token0_symbol
        self.token1_symbol = token1_symbol

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        acct = w3.eth.account.privateKeyToAccount(ethereum_wallet)
        # w3.eth.defaultAccount = acct

        self.w3 = w3
        self.acct = acct

        self.me = str(acct.address)

        self._check_approvals(self.token0_address)
        self._check_approvals(self.token1_address)

        self.notify(f"i am: {self.me}")

    def _get_abi(self, filename):
        path = pathlib.Path(__file__).parent.resolve()
        file = f'{path}/abi/{filename}.json'
        with open(file) as f:
            abi = json.load(f)
        return abi

    def _check_approvals(self, token: str):
        print("Checking approvals for %s" % token)
        erc20 = self.w3.eth.contract(str(token), abi=self._get_abi('erc20'))
        allowance = erc20.functions.allowance(
            str(self.me),
            str(self.seller_contract_address)
        ).call()

        if allowance == 0:
            infinity = 2**256 - 1
            tx = erc20.functions.approve(str(self.seller_contract_address), infinity).buildTransaction({
                'from': str(self.acct.address),
                'nonce': self.w3.eth.getTransactionCount(self.acct.address),
            })

            singedTx = self.acct.signTransaction(tx)
            tx_hash = self.w3.eth.sendRawTransaction(singedTx.rawTransaction)
            self.w3.eth.waitForTransactionReceipt(tx_hash)

    def notify(self, msg: str):
        self.logger().info(msg)

    def format_status(self):
        token0 = self.w3.eth.contract(str(self.token0_address), abi=self._get_abi('erc20'))
        token1 = self.w3.eth.contract(str(self.token1_address), abi=self._get_abi('erc20'))

        arthBalance18 = token0.functions.balanceOf(self.me).call()
        usdcBalance18 = token1.functions.balanceOf(self.me).call()

        arthBalance = arthBalance18 / 10 ** self.token0_decimals
        usdcBalance = usdcBalance18 / 10 ** self.token1_decimals

        etherscan = f'https://bscscan.com/address/${self.me}'

        return (
            f"I am [{self.me}]({etherscan}) and my balance is now `%d %s` and `%d %s` (Total: `$%d`)" % (
                arthBalance,
                self.token0_symbol,
                usdcBalance,
                self.token1_symbol,
                arthBalance * 2 + usdcBalance
            )
        )

    # After initializing the required variables, we define the tick method.
    # The tick method is the entry point for the strategy.
    def tick(self, timestamp):
        targetPriceContract = self.w3.eth.contract(str(self.seller_contract_address), abi=self._get_abi('TargetPriceUniswapBotV1'))
        token0 = self.w3.eth.contract(str(self.token0_address), abi=self._get_abi('erc20'))
        token1 = self.w3.eth.contract(str(self.token1_address), abi=self._get_abi('erc20'))

        arthBalance18 = token0.functions.balanceOf(self.me).call()
        usdcBalance18 = token1.functions.balanceOf(self.me).call()

        arthBalance = arthBalance18 / 10 ** self.token0_decimals
        usdcBalance = usdcBalance18 / 10 ** self.token1_decimals

        # print(arthBalance, usdcBalance, targetPriceContract.functions.executeArb)

        try:
            tx = targetPriceContract.functions.executeArb(str(self.pair_address), str(self.router_address)).buildTransaction({
                'from': str(self.acct.address),
                'nonce': self.w3.eth.getTransactionCount(self.acct.address),
            })

            singedTx = self.acct.signTransaction(tx)
            tx_hash = self.w3.eth.sendRawTransaction(singedTx.rawTransaction)
            etherscan_hash = f'https://bscscan.com/tx/${tx_hash}'

            self.notify(
                f'Executing arbitrage opportunity with a balance of `{arthBalance} {self.token0_symbol}`' +
                f'`{usdcBalance} {self.token1_symbol}` - [hash]({etherscan_hash})'
            )

            self.w3.eth.waitForTransactionReceipt(tx_hash)
            # print(receipt)

            arthBalance18 = token0.functions.balanceOf(self.me).call()
            usdcBalance18 = token1.functions.balanceOf(self.me).call()

            arthBalance = arthBalance18 / 10 ** self.token0_decimals
            usdcBalance = usdcBalance18 / 10 ** self.token1_decimals

            self.notify(
                "Moving on... My balance is now `%d %s` and `%d %s` (Total: `$%d`)" % (
                    arthBalance,
                    self.token0_symbol,
                    usdcBalance,
                    self.token1_symbol,
                    arthBalance * 2 + usdcBalance
                )
            )

        except ValueError as e:
            print(str(e))
