from flask import Flask, request
from hummingbot.client.hummingbot_application import HummingbotApplication
from threading import Thread
import asyncio


class SlackServer:
    hb: HummingbotApplication

    def __init__(self, instance: HummingbotApplication, ev_loop):
        self.hb = instance

    async def run(self, port=5002):
        api = Flask(__name__)

        def start_server():
            print('starting slack server on port', port)
            api.run(port=port, host="0.0.0.0")

        @api.route('/slack', methods=['POST'])
        def callback():
            command = request.json['command']
            try:
                asyncio.set_event_loop(self.hb.ev_loop)
                asyncio.get_event_loop().call_soon(lambda: self.hb._handle_command(command))
            finally:
                return "ok"

        thread_b = Thread(target=start_server, daemon=True)
        thread_b.start()
