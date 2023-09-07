#!/usr/bin/env bash

# 1. create softhsm token 
softhsm2-util --init-token --slot 0 --label "My token 1" --pin resigner:1234 --so-pin 1234
SOFTHSM_SLOT=$(softhsm2-util --show-slots | head -2 | sed -n 's/^Slot //p')

# 2. generate a ECDSA key pair in the HSM
HSM_USER='resigner'
HSM_PASSWORD='1234'
HSM_LIBFILE='/usr/local/lib/softhsm/libsofthsm2.so'
export GNUTLS_PIN="${HSM_USER}:${HSM_PASSWORD}"
P11TOOL="p11tool --provider ${HSM_LIBFILE}"
TOKEN=$(${P11TOOL} --list-tokens | head -2 | sed -n 's/\sURL:\s\(.*\)/\1/p')
${P11TOOL} --login --generate-ecc --label "MyNewKey" --outfile /dev/null "${TOKEN}"

# 3. get the public_handle, private_handle of the above key pair
HANDLES=$(
python3 - ${SOFTHSM_SLOT} ${GNUTLS_PIN}  ${HSM_LIBFILE} <<EOF 
from sys import argv
import pkcs11
hsm_slot = int(argv[1])
hsm_pin =  argv[2]
hsm_libfile = argv[3]
lib = pkcs11.lib(hsm_libfile)
slots = { slot.slot_id: slot for slot in  lib.get_slots() }
slot = slots.get(hsm_slot)
token = slot.get_token()
with token.open(user_pin=hsm_pin) as session:
    private_key = session.get_key(object_class=pkcs11.constants.ObjectClass.PRIVATE_KEY)
    public_key = session.get_key(object_class=pkcs11.constants.ObjectClass.PUBLIC_KEY)
    print(f'{private_key._handle}-{public_key._handle}')
EOF
)
IFS=- read -r PRIVATE_HANDLE PUBLIC_HANDLE  <<< ${HANDLES}

# 4. generate the config file for the service,
cat << EOF > /home/ec2-user/keys.json
{
    "hsm_username": "resigner",
    "hsm_slot": ${SOFTHSM_SLOT},
    "hsm_lib": "${HSM_LIBFILE}",
    "keys": {
        "tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW": {
            "public_key ": "p2pk67jx4rEadFpbHdiPhsKxZ4KCoczLWqsEpNarWZ7WQ1SqKMf7JsS",
            "private_handle": ${PRIVATE_HANDLE},
            "public_handle": ${PUBLIC_HANDLE} 
        }
    },
    "policy": {
        "baking": 1,
        "voting": ["pass"]
    }
}
EOF
