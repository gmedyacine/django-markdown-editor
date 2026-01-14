#!/usr/bin/env bash
set -euo pipefail

# Port exposé par Domino (souvent fourni par la plateforme)
PROXY_PORT="${PORT:-8888}"

# Trouver un port libre pour Phoenix en localhost
PHOENIX_INTERNAL_PORT="$(python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)"

export PHOENIX_ENABLE_AUTH=true
export PHOENIX_SECRET="${PHOENIX_SECRET:-change-me-32chars-min1digit1lower}"

# Proxy -> Phoenix
export PHOENIX_UPSTREAM="http://127.0.0.1:${PHOENIX_INTERNAL_PORT}"
export PHOENIX_ALT_AUTH_HEADER="${PHOENIX_ALT_AUTH_HEADER:-x-phoenix-api-key}"

echo "[INFO] Proxy will listen on :${PROXY_PORT}"
echo "[INFO] Phoenix will listen on 127.0.0.1:${PHOENIX_INTERNAL_PORT}"

# Nettoyage si le process s'arrête
cleanup() {
  echo "[INFO] Stopping background processes..."
  jobs -p | xargs -r kill || true
}
trap cleanup EXIT

# Lancer Phoenix en background (interne)
python3 -m phoenix.server.main --host 127.0.0.1 --port "${PHOENIX_INTERNAL_PORT}" serve &

# (Optionnel) attendre un peu que Phoenix démarre
sleep 2

# Lancer le proxy en foreground (exposé)
uvicorn proxy:app --host 0.0.0.0 --port "${PROXY_PORT}"
