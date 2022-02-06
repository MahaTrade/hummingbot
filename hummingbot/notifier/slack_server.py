from flask import Flask, request
from hummingbot.client.config.global_config_map import global_config_map
api = Flask(__name__)

verification_token = global_config_map.get("slack_verification_token").value


@api.route('/slack', methods=['POST'])
def start():
    from hummingbot.client.hummingbot_application import HummingbotApplication
    hb = HummingbotApplication.main_application()
    hb._handle_command(request.json['command'])
    return 'True'


def start_slack_server(port = 5002):
    print('starting slack server on port', port)
    api.run(port=port)
