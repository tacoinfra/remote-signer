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
${P11TOOL} --login --generate-ecc --label "MyNewKey" "${TOKEN}"

# 3. get the public_handle, private_handle of the above key pair
# HANDLES=$(
# python3 - ${SOFTHSM_SLOT} ${GNUTLS_PIN}  ${HSM_LIBFILE} <<EOF 
# import sys
# from pyhsm.hsmclient import HsmClient
# hsm_slot=int(sys.argv[1])
# hsm_pin = sys.argv[2]
# hsm_libfile= sys.argv[3]
# c = HsmClient(slot=hsm_slot, pin=hsm_pin, pkcs11_lib=hsm_libfile)
# public_handle, private_handle = c.find_objects() # 2,3
# print(f'{public_handle}-{private_handle}')
# EOF
# )
# IFS=- read -r PUBLIC_HANDLE PRIVATE_HANDLE <<< ${HANDLES}

# softhsm returns the handles in indeterminate order
# so we just pass in dummy values here and interrogate
# the API on each pkcs11 session
PRIVATE_HANDLE=2
PUBLIC_HANDLE=3

# 4. generate the config file for the service
cat << EOF > /keys.json
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

