#!/usr/bin/env python

import asyncio
import logging
import time
from typing import (
    AsyncIterable,
    Dict,
    Optional,
    List,
)
import json
import socketio
import hmac
import hashlib
import websockets
from websockets.exceptions import ConnectionClosed

from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.connector.exchange.coindcx.coindcx_auth import CoindcxAuth
from hummingbot.logger import HummingbotLogger
# from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.connector.exchange.coindcx.coindcx_order_book import CoindcxOrderBook

socketEndpoint = 'wss://stream.coindcx.com'
sio = socketio.Client()

sio.connect(socketEndpoint, transports = 'websocket')
api_key = '6b704411e1e416bac93dad3f17813e6ded5f23caff181b66'
secret_key = 'a1fd56eff81aec64d80f75e3b5b96390bdd3cfaade0608055d8106265335fbce'


COINDCX_USER_STREAM_ENDPOINT = "https://stream.coindcx.com"
MAX_RETRIES = 20
NaN = float("nan")

secret_bytes = bytes(secret_key, encoding='utf-8')

body = {"channel": "coindcx"}
json_body = json.dumps(body, separators = (',', ':'))
signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

sio.emit('join', {'channelName': 'coindcx', 'authSignature': signature, 'apiKey': api_key})


class CoindcxAPIUserStreamDataSource(UserStreamTrackerDataSource):

    MESSAGE_TIMEOUT = 30.0
    PING_TIMEOUT = 10.0

    _cbpausds_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._cbpausds_logger is None:
            cls._cbpausds_logger = logging.getLogger(__name__)
        return cls._cbpausds_logger

    def __init__(self, coindcx_auth: CoindcxAuth, trading_pairs: Optional[List[str]] = []):
        self._coindcx_auth: CoindcxAuth = coindcx_auth
        self._trading_pairs = trading_pairs
        self._current_listen_key = None
        self._listen_for_user_stream_task = None
        self._last_recv_time: float = 0
        self._socket_data: Dict = {}
        super().__init__()

    @property
    def socket_data(self):
        return self._socket_data

    @socket_data.setter
    def socket_data(self, data):
        self._socket_data = data

    @property
    def order_book_class(self):
        """
        *required
        Get relevant order book class to access class specific methods
        :returns: OrderBook class
        """
        return CoindcxOrderBook

    @property
    def last_recv_time(self) -> float:
        return self._last_recv_time

    async def listen_for_user_stream(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        """
        *required
        Subscribe to user stream via web socket, and keep the connection open for incoming messages
        :param ev_loop: ev_loop to execute this function in
        :param output: an async queue where the incoming messages are stored
        """
        while True:
            try:
                @sio.on('balance-update')
                def on_message(response):
                    self.data = response
                    self.socket_data = response
                    print('get_data', self.socket_data)
                output.put_nowait(self.socket_data)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unexpected error with Coinbase Pro WebSocket connection. "
                                    "Retrying after 30 seconds...", exc_info=True)
                await asyncio.sleep(30.0)

    async def _inner_messages(self,
                              ws: websockets.WebSocketClientProtocol) -> AsyncIterable[str]:
        """
        Generator function that returns messages from the web socket stream
        :param ws: current web socket connection
        :returns: message in AsyncIterable format
        """
        # Terminate the recv() loop as soon as the next message timed out, so the outer loop can reconnect.
        try:
            while True:
                try:
                    msg: str = await asyncio.wait_for(ws.recv(), timeout=self.MESSAGE_TIMEOUT)
                    self._last_recv_time = time.time()
                    yield msg
                except asyncio.TimeoutError:
                    pong_waiter = await ws.ping()
                    self._last_recv_time = time.time()
                    await asyncio.wait_for(pong_waiter, timeout=self.PING_TIMEOUT)
        except asyncio.TimeoutError:
            self.logger().warning("WebSocket ping timed out. Going to reconnect...")
            return
        except ConnectionClosed:
            return
        finally:
            await ws.close()


sio.emit('leave', {'channelName': 'coindcx'})
