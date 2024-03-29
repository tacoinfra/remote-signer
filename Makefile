all: check zipfile

#
#

DC=docker compose

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

down:
	${DC} stop

up:
	@${DC} up -d

rebuild:
	${DC} stop
	docker build -t remote-signer:latest .
	${DC} up --build --force-recreate --no-deps -d

int integration: up
	# We expect this to fail if the table already exists,
	# so we ignore that...
	${DC} exec signer sh -c '					\
		aws dynamodb create-table				\
		    --region eu-west-1					\
		    --endpoint http://dynamodb-local:8000		\
		    --table-name test					\
		    --attribute-definitions				\
			AttributeName=sig_type,AttributeType=S		\
		    --key-schema					\
			AttributeName=sig_type,KeyType=HASH		\
		    --provisioned-throughput				\
			ReadCapacityUnits=5,WriteCapacityUnits=5	\
		    --table-class STANDARD				\
		|| :'

	${DC} exec signer sh -c "pytest --cov=tezos_signer"

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
