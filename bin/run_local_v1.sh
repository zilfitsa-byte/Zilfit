#!/usr/bin/env bash
set -e

cd /root/hermes/zilfit-ip-core || exit 1
bash scripts/local/run_v1_local_stack.sh
