from setuptools import setup

setup(
    name='tezos-signer',
    version='0.9.9',
    packages=['tezos_signer'],
    scripts=['scripts/signer', 'scripts/start-remote-signer']
)
