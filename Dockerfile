FROM amazonlinux:2023

# update existing packages and install minimum build tools
RUN yum update -y && yum install -y wget unzip git

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

# update existing packages and install python3.11 alongside system python3
RUN yum update -y && yum install -y python3.11 python3.11-pip

# py-hsm depends on libhsm
# https://github.com/bentonstark/libhsm
RUN set -x; \
    BUILD_DEPS="make gcc g++"; \
    yum install -y ${BUILD_DEPS}; \
    cd /usr/src; \
    git clone https://github.com/tacoinfra/libhsm.git; \
    (cd ./libhsm/build; ./build_libhsm; cp libhsm.so /usr/lib64/libhsm.so); \
    yum remove -y ${BUILD_DEPS}

# create a directory structure like production
# and install dependencies in venv
#    /home/ec2-user
#    |-- env
#    |-- requirements.txt
#    |-- signer.py
#    `-- src
#        |-- __init__.py
#        |-- chainratchet.py
#        |-- ddbchainratchet.py
#        |-- hsmsigner.py
#        |-- signer.py
#        |-- sigreq.py
#        |-- start-remote-signer.sh
#        `-- validatesigner.py
COPY remote-signer.zip /home/ec2-user/
RUN set -x; \
    cd /home/ec2-user; \
    ZIP="remote-signer.zip"; \
    unzip ${ZIP}; \
    rm ${ZIP}; \
    python3.11 -m venv env; \
    source ./env/bin/activate; \
    python -m pip install -r ./requirements.txt; \
    # unhashable repos;  \
    pip install git+https://github.com/tacoinfra/py-hsm

# set up entrypoint to run this, requires these shell vars:
# REGION, HSMID DDB_TABLE, DD_MUTEX_TABLE_NAME
ENTRYPOINT [ "/home/ec2-user/src/start-remote-signer.sh" ]
