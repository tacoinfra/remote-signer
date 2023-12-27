
#
#

SRCS=	setup.py			\
	scripts/signer			\
	scripts/build-package-al2023	\
	scripts/setup-al2023		\
	tezos_signer/__init__.py	\
	tezos_signer/chainratchet.py	\
	tezos_signer/config.py		\
	tezos_signer/ddbchainratchet.py	\
	tezos_signer/hsmsigner.py	\
	tezos_signer/localsigner.py	\
	tezos_signer/signer.py		\
	tezos_signer/sigreq.py		\
	tezos_signer/validatesigner.py

ARCHFILES= $(SRCS) requirements.txt binaries/compat-openssl10.tar.xz

.PHONY: all check docker tarball zipfile

all: check zipfile

docker: tarball
	docker build -t remote-signer .

tarball: remote-signer.tar.gz

remote-signer.tar.gz: $(ARCHFILES)
	tar czf $@ $^

zipfile:
	zip remote-signer.zip requirements.txt *.py tezos_signer/*.py	\
	    scripts/*

check:
	python3 -m unittest test/test_remote_signer.py
