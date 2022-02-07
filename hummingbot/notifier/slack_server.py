from flask import Flask, request
from functools import wraps
from hummingbot.client.hummingbot_application import HummingbotApplication
from threading import Thread
import asyncio


def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped


class SlackServer:
    hb: HummingbotApplication

    def __init__(self, instance: HummingbotApplication, ev_loop):
        self.hb = instance

    async def run(self, port=5002):
        api = Flask(__name__)

        def start_server():
            print('starting slack server on port', port)
            api.run(port=port)

        @api.route('/slack', methods=['POST'])
        @async_action
        def callback():
            command = request.json['command']
            try:
                asyncio.set_event_loop(self.hb.ev_loop)
                asyncio.get_event_loop().call_soon(lambda: self.hb._handle_command(command))
            finally:
                return "ok"

        thread_b = Thread(target=start_server, daemon=True)
        thread_b.start()
