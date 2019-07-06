#!/bin/sh
# Starts the Remote Signer
# Written by Luke Youngblood, luke@blockscale.net
# -----------------------------------------------------------------------
# Requires the following environment variables to be set
# $REGION = the AWS region where the remote signer is deployed
# $HSMID = A unique identifier for the CloudHSM
# In addition, a Systems Manager parameter should be set that contains the following.
# This will be created automatically when you launch the CloudFormation template
# that creates the autoscaling group of remote signers:
# [
#	{
#	  "hsm_username": "${HSMUser}",
#	  "hsm_slot": ${HSMSlot},
#	  "hsm_lib": "${HSMLibFile}",
#	  "node_addr": "${NodeAddress}",
#	  "keys": {
#	    "${HSMPubKey}": {
#	      "hash": "${HSMPubKeyHash}",
#	      "private_handle": ${HSMPrivKeyHandle},
#	      "public_handle": ${HSMPubKeyHandle}
#	    }
#	  }
#	}
# ]

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

start_hsm_client() {
	# This client must be started in order for the PKCS#11 library to communicate with the CloudHSM
	sudo start cloudhsm-client
}

load_password() {
	# Loads the HSM password from SSM
	echo "Loading password from SSM..."
	export HSM_PASSWORD=`aws --region=$REGION ssm get-parameters \
		--name /hsm/$HSMID/password \
		--with-decryption \
		--output text \
		--query 'Parameters[*].Value'`
	if [ $? -ne 0 ]
	then
		echo "SSM Error retrieving password"
		exit 1
	fi
}

start_remote_signer() {
	echo "Starting remote signer..."
	cd /home/ec2-user
	FLASK_APP=signer /usr/local/bin/flask run --host=0.0.0.0
}

# main

start_hsm_client
load_password
start_remote_signer
