import requests
import json


class TezosRPCClient:
    TIMEOUT = 5.0  # seconds

    def __init__(self, node_url='localhost', node_port=8732):
        self.node_url = node_url
        self.node_port = node_port

    def send_request(self, uri, payload={}):
        url = 'http://{}:{}/{}'.format(self.node_url, self.node_port, uri)
        return requests.get(url, data=json.dumps(payload), timeout=self.TIMEOUT)

    def get_current_block(self):
        r = self.send_request('monitor/bootstrapped')
        return r.json()['block']

    def get_current_level(self):
        current_block = self.get_current_block()
        r = self.send_request('chains/main/blocks/{}/header'.format(current_block))
        return r.json()['level']
