# Tezos Remote Signer

This is a Python Flask app that receives messages from the Tezos baking client and passes them on to a remote HSM to be signed. This software uses the [py-hsm module](https://github.com/bentonstark/py-hsm) to support PKCS#11 signing operations, which means it should support the following HSMs:

* Gemalto SafeNet Luna SA-4
* Gemalto SafeNet Luna SA-5
* Gemalto SafeNet Luna PCIe K5/K6
* Gemalto SafeNet Luna CA-4
* SafeNet ProtectServer PCIe
* FutureX Vectera Series
* Cavium LiquidSecurity FIPS PCIe Card
* Utimaco Security Server Simulator (SMOS Ver. 3.1.2.3)
* OpenDNSSEC SoftHSM 2.2.0 (softhsm2)

Note that we have only tested it on [AWS CloudHSM](https://aws.amazon.com/cloudhsm/), which is based on the Cavium LiquidSecurity FIPS PCIe Card.

## Security Notes

Please note that this software does not provide any authentication or authorization. You will need to take care of that yourself. It simply returns the signature for valid payloads, after performing some checks:
* Is the message a valid payload?
* Does the message begin with a 0x01 or 0x02? Indicating it is a baking or endorsement, rather than a 0x03 transfer.
* Is the message within a certain threshold of the head of the chain? Ensures you are signing valid blocks.
* For baking signatures, is the block height of the payload greater than the current block height? This prevents double baking.

## Installation

Please note that you will need to install and compile your vendor's PKCS#11 C library before the py-hsm module will work.

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Execution

```
export HSM_PASSWORD=blah
FLASK_APP=signer flask run
```

## Running locally in docker against softhsm2
```sh

# build the docker containers and bring them up
make rebuild

# run the unit tests
make test

# show unit test coverage
make coverage

# run a few integration tests with the flask test client
make int

# lint
make lint

# static code analysis
make mypy

# open a shell in the signer container
make bash

# run the signer app in docker and make a signing request
make run
pip install httpie
http POST http://0.0.0.0:5000/keys/tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW <<<'"117a06a7700000000c0272b9c070cec8364f71d3361b0196ff250451241dc70933fefbda3b4c0eff329700000000619d27ce0401589994c43f991baf797f80702ba7f11075ea11eaed813c3b2eaf769b42ca30000000210000000102000000040000000c0000000000000004ffffffff0000000400000000c146ae2d2ada6afc75c4e2d84d994366d0944f1d5448f8ce5c99365ab8f7aa05532d7119ff62aeeea609473addaafc033aa264c5cf6ab8af70e1154ed44cb3d800000000ef9ad9f900000000ff408781a014bbc88d879ae2847cb65e31318c61aab34cd000ae27a9103a718b5b00"'
```
