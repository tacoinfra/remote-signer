#########################################################
# Written by Carl Youngblood, carl@blockscale.net
# Copyright (c) 2018 Blockscale LLC
# released under the MIT license
#########################################################

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging


class TezosRPCClient:
    TIMEOUT = 5.0  # seconds
    RETRIES = 3

    def __init__(self, node_url='http://localhost:8732'):
        self.node_url = node_url

    def send_request(self, uri):
        url = '{}/{}'.format(self.node_url, uri)
        logging.info('Performing get request {}'.format(url))
        response = None
        with requests.Session() as s:
            retries = Retry(
                total=self.RETRIES,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504])
            s.mount('http://', HTTPAdapter(max_retries=retries))
            s.mount('https://', HTTPAdapter(max_retries=retries))
            response = s.get(url, timeout=self.TIMEOUT)
            logging.info('Got response {}'.format(response))
        return response

    def get_current_block(self):
        r = self.send_request('monitor/bootstrapped')
        return r.json()['block']

    def get_current_level(self):
        current_block = self.get_current_block()
        r = self.send_request('chains/main/blocks/{}/header'.format(current_block))
        return r.json()['level']
