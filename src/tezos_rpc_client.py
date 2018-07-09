#########################################################
# Written by Carl Youngblood, carl@blockscale.net
# Copyright (c) 2018 Blockscale LLC
# released under the MIT license
#########################################################

import requests
import logging

class TezosRPCClient:
    TIMEOUT = 5.0  # seconds

    def __init__(self, node_url='http://localhost:8732'):
        self.node_url = node_url

    def send_request(self, uri):
        url = '{}/{}'.format(self.node_url, uri)
        logging.info('Performing get request {}'.format(url))
        response = requests.get(url, timeout=self.TIMEOUT)
        logging.info('Got response {}'.format(response))
        return response

    def get_current_block(self):
        r = self.send_request('monitor/bootstrapped')
        return r.json()['block']

    def get_current_level(self):
        current_block = self.get_current_block()
        r = self.send_request('chains/main/blocks/{}/header'.format(current_block))
        return r.json()['level']
