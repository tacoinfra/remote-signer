import requests
import json


class TezosRPCClient:
    def __init__(self, node_url='localhost', node_port=8732):
        self.node_url = node_url
        self.node_port = node_port

    def send_request(self, uri, payload={}):
        url = 'http://{}:{}/{}'.format(self.node_url, self.node_port, uri)
        return requests.post(url, data=json.dumps(payload))

    def get_current_block(self):
        r = self.send_request('bootstrapped')
        return r.json()['block']

    def get_current_level(self):
        current_block = self.get_current_block()
        r = self.send_request('blocks/{}/level'.format(current_block))
        return r.json()['level']
