FROM amazonlinux:2023

# install wget
RUN yum update -y && yum install -y wget

# Install and configure CloudHSM CLI
# https://docs.aws.amazon.com/cloudhsm/latest/userguide/gs_cloudhsm_cli-install.html
RUN	set -x; \
    TOP=https://s3.amazonaws.com/cloudhsmv2-software/CloudHsmClient	\
    VER=EL6 \
    CLIENT=cloudhsm-client-3.1.0-3.el6.x86_64.rpm \
    PKCS11=cloudhsm-client-pkcs11-3.1.0-3.el6.x86_64.rpm; \
    for i in $CLIENT $PKCS11; do \
        wget "$TOP/$VER/$i"; \
        yum install -y "$i"; \
        rm -f "$i"; \
    done; \
    /opt/cloudhsm/bin/configure -a hsm.internal

# install python 3.11
RUN yum install -y python3.11 python3.11-pip

# # build python 3 from source with openssl support and without replacing python
# ENV PYVERSION=3.11.5
# ENV BUILD_DEPS="yum-utils openssl-devel zlib-devel bzip2-devel libffi-devel perl make gcc"
# RUN set -x; \
#     yum install -y ${BUILD_DEPS}; \
#     yum-builddep -y python3; \
#     cd /usr/src; \
#     wget https://www.openssl.org/source/openssl-1.1.1v.tar.gz; \
#     tar -xzvf openssl-1.1.1v.tar.gz; \
#     cd openssl-1.1.1v; \
#     ./config --prefix=/usr --openssldir=/etc/ssl --libdir=lib no-shared zlib-dynamic; \
#     make; \
#     make install; \
#     cd /usr/src; \
#     wget https://www.python.org/ftp/python/${PYVERSION}/Python-${PYVERSION}.tgz; \
#     tar zxf Python-${PYVERSION}.tgz; \
#     rm Python-${PYVERSION}.tgz; \
#     cd Python-${PYVERSION}; \
#     ./configure --enable-optimizations --with-openssl=/usr; \
#     make altinstall


# py-hsm depends on libhsm
# https://github.com/bentonstark/libhsm
RUN set -x; \
    BUILD_DEPS="git make gcc g++"; \
    yum install -y ${BUILD_DEPS}; \
    cd /usr/src; \
    git clone https://github.com/bentonstark/libhsm.git; \
    (cd ./libhsm/build; ./build_libhsm; cp libhsm.so /usr/lib64/libhsm.so); \
    yum remove -y ${BUILD_DEPS}

COPY requirements.txt /

# install python dependencies in venv
RUN set -x;  \
    mkdir /src; \
    python3.11 -m venv /src/env; \
    source /src/env/bin/activate; \
    python -m pip install -r /requirements.txt; \
    rm /requirements.txt

# set up entrypoint
COPY src/. /src/
RUN chmod 755 /src/start-remote-signer.sh
COPY signer.py /
ENTRYPOINT ["/src/start-remote-signer.sh"]
