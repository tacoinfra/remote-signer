FROM amazonlinux:1

RUN \
	yum install -y wget aws-cli python36 python36-devel git gcc &&	\
	easy_install-3.6 pip

RUN	TOP=https://s3.amazonaws.com/cloudhsmv2-software/CloudHsmClient	\
	VER=EL6								\
	CLIENT=cloudhsm-client-3.1.0-3.el6.x86_64.rpm			\
	PKCS11=cloudhsm-client-pkcs11-3.1.0-3.el6.x86_64.rpm;		\
									\
	for i in $CLIENT $PKCS11; do					\
		wget "$TOP/$VER/$i";					\
		yum install -y "$i";					\
		rm -f "$i";						\
	done

RUN \
	/opt/cloudhsm/bin/configure -a hsm.internal && \
	pip3 install -r /requirements.txt && \
	chmod 755 /src/start-remote-signer.sh && \
	yum clean all

COPY src/. /src/
COPY signer.py /
COPY requirements.txt /

ENTRYPOINT ["/src/start-remote-signer.sh"]
