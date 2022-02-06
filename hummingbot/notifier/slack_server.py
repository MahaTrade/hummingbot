from flask import Flask, request
from hummingbot.client.hummingbot_application import HummingbotApplication
import asyncio
from functools import wraps


def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped


class SlackServer:
    hb: HummingbotApplication
    api: Flask

    def __init__(self, instance: HummingbotApplication, ev_loop):
        self.hb = instance
        self.ev_loop = ev_loop

    async def run(self, port=5002):
        print('starting slack server on port', port)
        asyncio.set_event_loop(asyncio.new_event_loop())
        api = Flask(__name__)

        @api.route('/slack', methods=['POST'])
        @async_action
        async def start():
            command = request.json['command']
            self.hb._notify('ok got' + command)

            output = f"\n[Slack Input] {command}"
            self.hb.app.log(output)

            # await safe_ensure_future(self.hb._handle_command, command, loop=self.ev_loop)
            return "ok"

        self.api = api
        self.api.run(port=port)
