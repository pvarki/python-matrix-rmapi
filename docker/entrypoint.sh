#!/bin/bash -l
# shellcheck disable=SC1091
. /container-init.sh

set -e
if [ "$#" -eq 0 ]; then
  # FIXME: can we know the traefik/nginx internal docker ip easily ?
  exec gunicorn "rmfpapi.app:get_app()" --bind 0.0.0.0:8001 --forwarded-allow-ips='*' -w 4 -k uvicorn.workers.UvicornWorker
else
  exec "$@"
fi
