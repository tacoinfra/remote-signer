FROM amazonlinux:2023

COPY tezos_signer/.	/tezos_signer/
COPY scripts/.		/scripts/
COPY setup.py		/
COPY requirements.txt	/

RUN  scripts/build-package-al2023

ENTRYPOINT ["/usr/local/bin/start-remote-signer"]
