#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

locustfile=${LOCUSTFILE:-}
args=${LOCUST_ARGS:-}

# Distributed workers
num_workers=${LOCUST_WORKERS:-'10'}
workers=()
for i in $(seq 1 "${num_workers}")
do
    poetry run locust -f "${locustfile}" --worker --master-host localhost --timescale &
    workers[${#workers[@]}]=$!
done

# Run master
poetry run locust -f "${locustfile}" ${args} \
    --master \
    --expect-workers "${num_workers}" \
    --timescale

# Ensure workers all quit
kill ${workers[@]} || true
