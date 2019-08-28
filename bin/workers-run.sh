#!/bin/bash

set -eu -o pipefail

# CELERY_TRACE_APP=1 ANSIBLE_DEBUG=1 ANSIBLE_VERBOSITY=6 \
exec env -i bash --noprofile --norc <<'EOF'
  set -eu

  cleanup() {
    echo
    echo Exiting ..
  }
  trap 'cleanup' INT QUIT EXIT

  echo
  date +%FT%T
  echo Initializing environment ..
  source venv/bin/activate

  echo -n '  ansible:   '; command -v ansible
  echo -n '  terraform: '; command -v terraform
  echo

  watchmedo auto-restart --directory=./apis/ --pattern=*.py --recursive -- \
  celery worker -A apis.v1.tasks.celery \
    -O fair \
    --concurrency 1 \
    --heartbeat-interval 3 \
    --loglevel=info \
    --max-tasks-per-child 1 \
    --task-events \
    --without-gossip \
    --without-mingle

  kill 0
EOF

# TODO
# "CELERY_LOG_FILE": "",
# "CELERY_LOG_LEVEL": "20",
# "CELERY_LOG_REDIRECT": "1",
# "CELERY_LOG_REDIRECT_LEVEL": "WARNING",
