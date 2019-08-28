#!/bin/bash

# Start the app in a super-clean environment
exec env -i bash --noprofile --norc <<'EOF'
  DIR=$( cd "${BASH_SOURCE[0]##*/}" && pwd )
  source "$DIR/env.sh"

  source venv/bin/activate

  FLASK_APP="${FLASK_APP:-app.py}" \
  watchmedo auto-restart --directory=./apis/ --pattern=*.py --recursive -- \
    python3 -m flask run --reload
EOF
