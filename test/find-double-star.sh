#!/bin/sh

#
# This script will find evidence of double baking, endorsing, and
# pre-endorsing.  We make a few assumptions about the structure of JSON
# returned from our queries.  Most importantly, that all operation kinds
# that involve slashing end in the string "evidence" and no operation
# kind which doesn't involve slashing will end in said string.

TOP=http://127.0.0.1:8732/chains/main

#
# We slip backwards through time to the beginning looking for
# evidence:

CUR=head
while :; do
	echo $CUR
	JSON="$(curl -s "$TOP/blocks/$CUR")"

	if [ $? -gt 0 ]; then
		echo "FAILED" 1>&2
		echo $JSON 1>&2
		exit 1
	fi

	CUR="$(echo "$JSON" | jq -r .header.predecessor)"

	echo "$JSON" | jq -c '[ .header.level
			   , ( .operations[][].contents[]
			       |select(.kind|match("evidence$"))
			       |.metadata.balance_updates[]
			       |select(.category == "deposits")
			       |.delegate)
			   ]
			'
done
