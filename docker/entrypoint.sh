#!/bin/bash -l
# shellcheck disable=SC1091
. /container-init.sh

mkdir -p /ui_files/matrix
if [ -d "/ui_build" ]; then
    echo "Copying UI files from /ui_build → /ui_files/matrix ..."
    cp -r /ui_build/* /ui_files/matrix/
else
    echo "No UI found at /ui_build, skipping copy."
fi

set -e
if [ "$#" -eq 0 ]; then
  # FIXME: can we know the traefik/nginx internal docker ip easily ?
  exec gunicorn "matrixrmapi.app:get_app()" --bind 0.0.0.0:8012 --forwarded-allow-ips='*' -w 4 -k uvicorn.workers.UvicornWorker
else
  exec "$@"
fi
