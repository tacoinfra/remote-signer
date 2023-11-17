from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='tezos-signer',
    version='0.9.9',
    packages=['tezos_signer'],
    scripts=['scripts/signer', 'scripts/setup-al2023'],
    install_requires=requirements,
)
