import os
import json
from websocket import create_connection

class PusherClient:

    def __init__(self, user_id):

        host = os.getenv('MOS_BACKEND_HOST', 'localhost')
        port = os.getenv('MOS_BACKEND_PORT', '8000')
        if port == '443':
            ws = 'wss'
        else:
            ws = 'ws'
        self.ws = create_connection('{ws}://{host}:{port}/ws/notifications/{user_id}/'.format(
            ws=ws,
            host=host,
            port=port,
            user_id=user_id 
        )) 

    def send(self, msg):

        self.ws.send(json.dumps(msg))
