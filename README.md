# Tezos Remote Signer

This is a Python Flask app that receives messages from the Tezos baking client and passes them on to the a remote HSM to be signed. This software uses the [py-hsm module](https://github.com/bentonstark/py-hsm) to support PKCS#11 signing operations, which means it should support the following HSMs:

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

## Running the tests
```
export HSM_PASSWORD=blah
python -m unittest test/test_remote_signer.py
```

## Assistance

If you would like assistance implementing this in a production/secure environment, with high availability, authentication, and authorization, please contact us at contact -at- blockscale.net.