#!/usr/bin/env bash
set -e

# Load profile to restore PATH, pnpm, poetry env, etc.
export PATH=/root/.local/bin:/ui/node_modules/.bin:$PATH

echo "Installing dev dependencies..."
pnpm --dir /ui install

/app/docker/container-init.sh

poetry install

mkdir -p /ui_files/matrix

echo "Starting pnpm build --watch..."
pnpm --dir /ui build --outDir /ui_files/matrix --watch &

echo "Starting uvicorn..."
poetry run uvicorn --host 0.0.0.0 --port 8012 --log-level debug \
    --factory matrixrmapi.app:get_app --reload
