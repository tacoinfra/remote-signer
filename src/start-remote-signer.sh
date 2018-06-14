#!/bin/sh
# Starts the Remote Signer
# Written by Luke Youngblood, luke@blockscale.net
# -----------------------------------------------------------------------
# Requires the following environment variables to be set
# $REGION = the AWS region where the remote signer is deployed
# $HSMADDR = The FQDN or IP address of the CloudHSM
# $HSMID = A unique identifier for the CloudHSM
# $HSMSLOT = The slot in the CloudHSM we are using, typically 1
# $HSM_KEY_HANDLE = The handle of the private key that we will use to sign
# $HSM_USER = The username we will login to the CloudHSM with
# $HSM_PASSWORD = The password we will login to the CloudHSM with
# $HSM_LIBFILE = Typically /opt/cloudhsm/lib/libcloudhsm_pkcs11.so
# $RPC_ADDR = The FQDN or IP address of the Tezos node
# $RPC_PORT = The port that the node is listening on, typically 8732

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

start_hsm_client() {
	echo "Configuring CloudHSM address..."

	/opt/cloudhsm/bin/configure -a $HSMADDR
	cd /opt/cloudhsm/run
	exec /opt/cloudhsm/bin/cloudhsm_client /opt/cloudhsm/etc/cloudhsm_client.cfg >> /opt/cloudhsm/run/cloudhsm_client.log &
	cd /
}

restore_ssl_cert() {
	# Restore the customerCA.crt file from SSM
	echo "Restoring customerCA.crt from SSM..."
	aws --region=$REGION ssm get-parameters \
		--name /hsm/$HSMID/customerCA.crt \
		--with-decryption \
		--output text | sed 's/.*-----BEGIN/-----BEGIN/' | sed 's/CERTIFICATE-----.*/CERTIFICATE-----/' \
		> /opt/cloudhsm/etc/customerCA.crt
	if [ $? -ne 0 ]
	then
		echo "SSM Error retrieving customerCA.crt"
		#exit 1
	else
		cat /opt/cloudhsm/etc/customerCA.crt
	fi

	# Restore the HSM password from SSM
	echo "Restoring password from SSM..."
	HSM_PASSWORD=`aws --region=$REGION ssm get-parameters \
		--name /hsm/$HSMID/password \
		--with-decryption \
		--output text | cut -f 4`
	if [ $? -ne 0 ]
	then
		echo "SSM Error retrieving password"
		#exit 1
	fi
}

start_remote_signer() {
	echo "Starting remote signer..."
	cd /
	FLASK_APP=signer flask run
}

monitor() {
	# This function monitors the CloudHSM client and remote signer and restarts them if necessary.
	while true
	do
		sleep 60
	done
}

# main

start_hsm_client
restore_ssl_cert
start_remote_signer
monitor
