from flask import Flask, request
from hummingbot.client.hummingbot_application import HummingbotApplication


class SlackServer:
    hb: HummingbotApplication

    def __init__(self, instance: HummingbotApplication):
        self.hb = instance

    async def start_slack_server(self, port = 5002):
        api = Flask(__name__)

        @api.route('/slack', methods=['POST'])
        def start():
            command = request.json['command']
            self.hb._handle_command(command)
            return "ok"

        print('starting slack server on port', port)
        api.run(port=port)
