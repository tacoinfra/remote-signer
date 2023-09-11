#!/bin/bash
HITS=$(grep -R --include \*.py "^\s\+from IPython")
if [[ -n "${HITS}" ]]
then
    echo ${HITS}
    exit 1
else
    exit 0
fi
