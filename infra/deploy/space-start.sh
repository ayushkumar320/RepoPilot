#!/bin/sh
# Redis + arq worker + API in one container. See infra/deploy/Dockerfile.space.
set -e

redis-server --daemonize yes --save "" --appendonly no
until redis-cli ping >/dev/null 2>&1; do sleep 0.2; done

arq repopilot_api.jobs.index_repo.WorkerSettings &
worker_pid=$!

# If the worker dies, the box stops indexing but keeps answering — which looks
# like a hang to anyone who pastes a repo. Take the container down instead so
# the Space restarts it.
trap 'kill "$worker_pid" 2>/dev/null' INT TERM EXIT
(while kill -0 "$worker_pid" 2>/dev/null; do sleep 5; done; echo "arq worker exited" >&2; kill 1) &

exec uvicorn repopilot_api.app:app \
  --app-dir apps/api/src \
  --host 0.0.0.0 \
  --port "${PORT:-7860}" \
  --timeout-keep-alive 75
