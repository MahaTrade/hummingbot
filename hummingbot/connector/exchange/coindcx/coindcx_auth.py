# import base64
import json
# import time
import hashlib
import hmac
from typing import (
    Any,
    Dict
)


class CoindcxAuth:
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    def add_auth_to_params(self, args: Dict[str, Any] = None) -> Dict[str, Any]:

        # args.update(timestamp= int(round(time.time() * 1000)))
        secret_bytes = bytes(self.secret_key, encoding='utf-8')

        json_body = json.dumps(args, separators = (',', ':'))

        signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }

        return headers
