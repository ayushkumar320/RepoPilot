#!/bin/sh
# Ollama entrypoint that preloads the models the rest of the stack needs.
#
# Models are listed in $OLLAMA_PRELOAD_MODELS (space-separated). We start the
# Ollama server in the background, wait for it to accept connections, pull each
# model if it isn't already cached, then hand control to the foreground server
# so docker-compose can health-check it.
#
# Idempotent: if a model is already present in the named volume, `ollama pull`
# is a no-op (it diffs blobs and exits quickly).

set -eu

PRELOAD_MODELS="${OLLAMA_PRELOAD_MODELS:-qwen2.5-coder:7b nomic-embed-text}"

echo "[ollama-entrypoint] starting server in background"
/bin/ollama serve &
OLLAMA_PID=$!

# Wait for the API to come online.
for i in $(seq 1 60); do
    if /bin/ollama list >/dev/null 2>&1; then
        echo "[ollama-entrypoint] server is up"
        break
    fi
    sleep 1
done

for model in $PRELOAD_MODELS; do
    echo "[ollama-entrypoint] ensuring model '$model' is cached"
    /bin/ollama pull "$model" || {
        echo "[ollama-entrypoint] WARN: pull failed for $model (will retry on first use)"
    }
done

echo "[ollama-entrypoint] preload complete; handing off to server (pid=$OLLAMA_PID)"
wait "$OLLAMA_PID"
