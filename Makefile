


all: check zipfile

docker:
	docker build -t remote-signer .

tarball: remote-signer.tar.gz

.PHONY: remote-signer.tar.gz
remote-signer.tar.gz:
	tar czf $@ requirements.txt *.py tezos_signer scripts

zipfile:
	zip remote-signer.zip requirements.txt *.py tezos_signer/*.py	\
	    scripts/*

check:
	python3 -m unittest test/test_remote_signer.py
