# import base64
# import json
import time
import hashlib
import hmac
import string
import random

from typing import (
    Any,
    Dict
)
# from collections import OrderedDict


class LbankAuth:
    def __init__(self, api_key: str, secret_key: str):
        self.api_key: str = api_key
        self.secret_key: str = secret_key

    def buildHmacSHA256(self, params, secret_key, t):
        '''build the signature of the HmacSHA256'''

        p = params

        p["timestamp"] = t
        p["signature_method"] = 'HmacSHA256'
        par = []
        for k in sorted(p.keys()):
            par.append(k + '=' + str(p[k]))
        par = '&'.join(par)
        msg = hashlib.md5(par.encode("utf8")).hexdigest().upper()

        appsecret = bytes(secret_key, encoding='utf8')
        data = bytes(msg, encoding='utf8')
        signature = hmac.new(appsecret, data, digestmod=hashlib.sha256).hexdigest().lower()

        return signature

    def add_auth_to_params(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        par = args
        num = string.ascii_letters + string.digits
        randomstr = "".join(random.sample(num, 35))

        t = str(round(time.time() * 1000))

        header = {"Accept-Language": 'zh-CN', "signature_method": "HmacSHA256", 'timestamp': t, 'echostr': randomstr}

        par['echostr'] = randomstr

        sign = self.buildHmacSHA256(params=par, secret_key=self.secret_key, t=t)

        par['sign'] = sign

        del par["timestamp"]
        del par["signature_method"]

        response = {
            "header": header,
            "par": par
        }

        return response
