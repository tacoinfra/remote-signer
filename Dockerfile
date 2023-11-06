FROM amazonlinux:2023

COPY requirements.txt /

RUN	set -e;								\
	BUILD_DEPS="python3-pip python3-devel gcc git-core";		\
	BUILD_DEPS="$BUILD_DEPS libsodium-devel gmp-devel";		\
	yum update -y;							\
	yum install -y	libsodium gmp					\
			$BUILD_DEPS;					\
									\
	TOP=https://s3.amazonaws.com/cloudhsmv2-software/CloudHsmClient	\
	VER=EL6								\
	CLIENT=cloudhsm-client-3.1.0-3.el6.x86_64.rpm			\
	PKCS11=cloudhsm-client-pkcs11-3.1.0-3.el6.x86_64.rpm;		\
									\
	for i in $CLIENT $PKCS11; do					\
		curl -o "$i" "$TOP/$VER/$i";				\
		yum install -y "$i";					\
		rm -f "$i";						\
	done;								\
	/opt/cloudhsm/bin/configure -a hsm.internal;			\
									\
	pip3 --no-cache install setuptools==68.2.2;			\
	pip3 --no-cache install -r /requirements.txt;			\
									\
	yum remove -y $BUILD_DEPS;

COPY tezos_signer/.	/tezos_signer/
COPY scripts/.		/scripts/
COPY setup.py		/

RUN	set -e;								\
	yum install -y python3-pip;					\
	pip3 --no-cache install .;					\
	yum remove -y python3-pip;

ENTRYPOINT ["/usr/local/bin/start-remote-signer"]
