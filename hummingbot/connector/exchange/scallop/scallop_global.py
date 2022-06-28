import aiohttp
from hummingbot.connector.exchange.scallop.scallop_auth import ScallopAuth
from hummingbot.connector.exchange.scallop.scallop_rest_api import ScallopRestApi


class ScallopGlobal:

    def __init__(self, key: str, secret: str):
        self.auth = ScallopAuth(key, secret)
        self.rest_api = ScallopRestApi(self.auth, self.http_client)
        self._shared_client: aiohttp.ClientSession = None

    async def http_client(self) -> aiohttp.ClientSession:
        """
        :returns Shared client session instance
        """
        if self._shared_client is None:
            self._shared_client = aiohttp.ClientSession()
        return self._shared_client
