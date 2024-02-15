# Tezos Remote Signer

This is a Python Flask app that implements a Tezos Remote Signer.
It receives messages from the Tezos baking client and returns signatures
after applying policy and/or using an HSM.

## Configuration

Configuration is via a file in the current working directory called
`keys.json` which is, as one would expect, a JSON file.  Here is a
quick example for a local signer:

```
{
	"ratchet": "mockery",
	"keys": {
		"tz1ZjN1B5a...": {
			"signer": "local",
			"public_key": 'edpkuH1HEpS...",
			"secret_key": 'edsk3t9PBQg..."
		}
	},
	"policy": {
		"baking": 1,
		"voting": ["aye", "pass"]
	}
}
```

This configuration will sign baking requests for the configured key.
It will also allow votes to be cast as long as they are all "aye" or
"pass".

Here are all of the possible values:

|Key          |Value                                               |
|-------------|----------------------------------------------------|
|chain_ratchet|string naming the chain ratchet used                |
|keys         |either a string or a dictionary, documented below   |
|policy       |dictionary, documented below                        |
|hsm_username |string: self-explanatory                            |
|hsm_slot     |int: self-explanatory                               |
|hsm_lib      |string: self-explanatory?                           |
|aws_region   |string: self-explanatory                            |
|bind_addr    |IP address defaulting to 127.0.0.1                  |
|bind_port    |int defaulting to 5000                              |
|ddb_table    |string: name of DDB table for DynamoDB chain ratchet|

### keys

Keys must be a dictionary where each key is a secret key, public key, or
public key hash.  Using a public key hash is deprecated and kept only for
compatibility with older configurations.  If a public key hash is used,
then the public key must be provided in the key definition.

The value associated with each key is either a string or a dictionary.
Using a dictionary is deprecated and will not be documented here.

If it is a string, then it will be interpreted as a colon separated
list of values.  The first value must be either a public or secret key.
The second value is the name of the signer which will be used with
this key.  And all additional values will be passed to the signer as
arguments and therefore depend on which signer is used.

Any fields that are implied can be elided.  E.g. if you provide a secret
key, then you don't need to specify anything else as it will default to a
"local" signer.

Valid signers are: local and amazon_hsm.

## Signer Class

Other than a constructor, objects of class Signer implement a single
method `sign` which takes a `SignatureRequest` object returning a
signature encoded as a base58 string with the appropriate prefix.
The config and, perhaps, the key must be passed to initialise the signer.

### ValidateSigner

This class applies local policy to the request (validates) and if said
policy allows, passes the request to a configured "subsigner" which may
sign the request.  This class is called regardless of the configuration
in `keys.json`, but the configuration will control its behaviour.

First, a ValidateSigner will evaluate the policy block defined in
`keys.json` and ensure that the request complies with it.  "policy" is a
dictionary and we currently define two keys: "baking" and "voting".  The
former is a boolean and if true then all baking requests (preendorsement,
endoresement, block) are allowed.  The latter is a list of strings:
"aye", "nay", or "pass".  If this is defined then votes matching any of
the string in the list are allowed.

Next, a ChainRatchet is applied if the SignatureRequest is of type
"baking".  This is sometimes called a watermark in other remote signers.
It is a mechanism by which we ensure that we do not sign baking requests
at a level and round less than or equal to a similar request that we
have already signed.  In doing this, we provide an additional control
which prevents double baking.

After this, ValidateSigner will call the configured "subsigner" which
will should return a valid signature.

### LocalSigner

This is an implementation of Signer which signs in software from secret
keys that are configured in `keys.json`.  The example above shows the
way to define them.

This class makes a good example of how to add your own signer.

### HsmSigner

This class uses the
[py-hsm module](https://github.com/bentonstark/py-hsm) to
support PKCS#11 signing operations, which means it should support the
following HSMs:

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

### MockSigner

This one is just used for unit testing and may be deprecated in the
future as LocalSigner should be good enough for unit tests.

### Writing your own Signer

The basic structure of a signer is, as mentioned above, a class with
an initialiser and a single method named `sign`.  This method takes
a public key hash encoded in base58 and a SignatureRequest and should
return a base58 encoded signature.

Here is some example code:

```
import logging
import threading

from tezos_signer import Signer

class MyHSMSigner(Signer):
    def __init__(self, config, key):
        # The config  is passed in, variables can be
        # extracted and used here.
        self.key = key
        self.hsm = connect_to_my_hsm()
        # If we need locking:
        self.lock = threading.Lock()

    def sign(self, sigreq):
        # Now, we hash the data in the way the Tezos expects.
        # Note that this step is not required if the signature
        # code already does it, e.g. pytezos Key.sign() does
        # this for you.

        with self.lock:
            self.hsm.sign(data=sigreq.get_hashed_payload(), OTHER ARGS)

        # And our parent class has a method to base58 encode the
        # result in the correct way for us.  Again, note that this
        # isn't necessary for the local signer as pytezos Key.sign()
        # does this for you.

        return Signer.b58encode_signature(sig)
        
```

## ChainRatchet class

A ChainRatchet keeps track of what level and round previous baking
operations were signed and helps the remote-signer refuse to sign further
requests at the same or lower levels in order to provide an additional
protection against double baking.

All children are expected to inherit from ChainRatchet and implement
both a constructor (`__init__`) and a method `check`.  The constructor
takes a TacoinfraConfig, a level, and a round.

The `check` method takes three arguments: signature type, level, and
round.  `check` must ensure that all previous calls to it across all
running instances of `remote-signer` have not received a valid signature
for the signature type and the level/round at or below the previous max.
`ChainRatchet` provides a `check` method which can be used.

ChainRatchet's are expected to throw exceptions on failure.  For best
results, import werkzeug's abort function and use it:

```
from werkzeug.exceptions import abort

    abort(410, f"Will not sign {level}/{round} because ratchet " +
               f"has seen {self.lastlevel}/{self.lastround}")
```

A pseudocode example would be:

```
class MyChainRatchet:
    def __init__(self, config):
        self.db = connect_to_my_db(config.get_ddb_table())

    def check(self, sig_type, level, round):
        # These operations must be performed under a lock, unless you
        # have some interesting DB logic which achieves the same result.
        with self.db.lock():
            # First we update our object's idea of what levels and rounds
            # have come before by consulting our external data source

            self.lastlevel, self.lastround = self.db.get_levelround(sig_type)

            # The parent class' check method will throw an appropriate
            # exception if self.lastlevel, self.lastround are the same
            # or greater than the level and round passed in.

            super().check(sig_type, level, round)

            # NOTE: it is very important that an exception is thrown if
            # you are unable to update the backend storage with the new
            # level and round information or you may allow double baking.

            self.db.update_db(sig_type, level, round)
```

In the above example, we refer to "interesting DB logic which achieves
the same result".  This could be an atomic test and set operation if
your datastore supports it.

### DDBChainRatchet

This ChainRatchet uses Amazon AWS' DynamoDB as a backend to store the
current level and round.  To configure it, you need to set two config
variables: `aws_region` and `ddb_table`.  `ddb_table` is name of the table
within DynamoDB that your ratchet is stored.  These are documented above.

### MockChainRatchet

This ChainRatchet stores the current level and round in memory and is
used in testing because the level and round are not persistent between
invocations.

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

## Running the tests

```
make check
```
