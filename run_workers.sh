#!/bin/bash
set -euo pipefail

python3 -m core.discovery &
python3 -m core.validator &
python3 -m core.indexer &
wait
