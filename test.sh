#!/usr/bin/env bash

. venv/bin/activate
echo “Testing lambda”
python-lambda-local -f $1 $2 $3