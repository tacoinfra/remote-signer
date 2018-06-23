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
#	  "hsm_address": "${HSMAddress}",
#	  "hsm_username": "${HSMUser}",
#	  "hsm_slot": ${HSMSlot},
#	  "hsm_lib": "${HSMLibFile}",
#	  "rpc_addr": "${NodeAddress}",
#	  "rpc_port": "${RPCPort}",
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
ROLE=`curl http://169.254.169.254/latest/meta-data/iam/security-credentials/`
export AWS_ACCESS_KEY_ID=`curl http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE | jq -r '.AccessKeyId'`
export AWS_SECRET_ACCESS_KEY=`curl http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE | jq -r '.SecretAccessKey'`
export AWS_SESSION_TOKEN=`curl http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE | jq -r '.Token'`
export AWS_REGION=$REGION

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
		--output text | cut -f 4`
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

monitor() {
	# This function monitors the CloudHSM client and remote signer and restarts them if necessary.
	while true
	do
		sleep 60
	done
}

# main

start_hsm_client
load_password
start_remote_signer
#monitor
