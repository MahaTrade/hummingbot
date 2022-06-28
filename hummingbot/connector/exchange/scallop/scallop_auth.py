import hmac
import hashlib
import base64
# from os import times
import aiohttp
from typing import List, Dict, Any
# from hummingbot.connector.exchange.scallop.scallop_utils import get_ms_timestamp
from hummingbot.connector.exchange.scallop import scallop_constants as Constants
from hummingbot.connector.exchange.scallop.time_patcher import TimePatcher


_time_patcher: TimePatcher = None


def time_patcher() -> TimePatcher:
    global _time_patcher
    if _time_patcher is None:
        _time_patcher = TimePatcher('Scallop', ScallopAuth.query_time_func)
        _time_patcher.start()
    return _time_patcher


class ScallopAuth():
    """
    Auth class required by scallop API
    Learn more at https://exdocs.gitbook.io/v/v/english
    """

    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.time_patcher = time_patcher()
        # self.time_patcher = time

    @classmethod
    async def query_time_func() -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(Constants.REST_URL + '/sapi/v1/time') as resp:
                resp_data: Dict[str, float] = await resp.json()
                return int(resp_data["serverTime"])

    def get_private_headers(
        self,
        method: str,
        path_url: str,
        data: Dict[str, Any] = None
    ):
        data = ''
        nonce = int(self.time_patcher.time())

        if(len(str(int(self.time_patcher.time()))) != 13):
            nonce = int(self.time_patcher.time() * 1000)

        if data is not {}:
            data = str(nonce) + method.upper() + path_url + str(data)
        else:
            data = str(nonce) + method.upper() + path_url

        payload = data
        print('payload', payload)
        sig = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        header = {
            'X-CH-APIKEY': self.api_key,
            'X-CH-SIGN': sig,
            'X-CH-TS': str(nonce),
        }
        print(header)
        return header

    def generate_ws_signature(self) -> List[Any]:
        data = [None] * 3
        data[0] = self.api_key
        nonce = int(self.time_patcher.time() * 1000)
        data[1] = str(nonce)

        data[2] = base64.b64encode(hmac.new(
            self.secret_key.encode('latin-1'),
            f"{nonce}".encode('latin-1'),
            hashlib.sha256
        ).digest())

        return data
