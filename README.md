# IMPORTANT NOTICE

*This project is no longer maintained. Amazon are migrating their customers
from SDK3 to SDK5 and also HSMv1 to HSMv2. You should have received
notice from them.*

**What to do:** ECAD Labs has released Signatory 1.2.0 which supports 
CloudHSMv2. This significantly reduces the complexity of using CloudHSM.

# Tezos Remote Signer

This is a Python Flask app that implements a Tezos Remote Signer.
It receives messages from the Tezos baking client and returns signatures
after applying policy and/or using an HSM.

The configuration instructions have moved to INSTALL.md.
