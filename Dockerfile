FROM amazonlinux:1

COPY src/. /src/
COPY signer.py /
COPY requirements.txt /

RUN \
	yum install -y wget aws-cli python36 python36-devel git gcc && \
	easy_install-3.6 pip && \
	wget https://s3.amazonaws.com/cloudhsmv2-software/CloudHsmClient/AmazonLinux/cloudhsm-client-latest.amzn1.x86_64.rpm && \
	yum install -y ./cloudhsm-client-latest.amzn1.x86_64.rpm && \
	rm -f ./cloudhsm-client-latest.amzn1.x86_64.rpm && \
	wget https://s3.amazonaws.com/cloudhsmv2-software/CloudHsmClient/AmazonLinux/cloudhsm-client-pkcs11-latest.amzn1.x86_64.rpm && \
	yum install -y ./cloudhsm-client-pkcs11-latest.amzn1.x86_64.rpm && \
	rm -f ./cloudhsm-client-pkcs11-latest.amzn1.x86_64.rpm && \
	/opt/cloudhsm/bin/configure -a hsm.internal && \
	pip3 install -r /requirements.txt && \
	chmod 755 /src/start-remote-signer.sh && \
	yum clean all

ENTRYPOINT ["/src/start-remote-signer.sh"]
