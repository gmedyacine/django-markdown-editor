set -euo pipefail

# (tes exports existants)
export PHOENIX_ENABLE_AUTH=true
export PHOENIX_SECRET="change-me-32chars-min1digit1lower"

# Phoenix doit écouter en interne (pas sur le port exposé)
export PHOENIX_INTERNAL_PORT=8899
export PHOENIX_UPSTREAM="http://127.0.0.1:${PHOENIX_INTERNAL_PORT}"
export PHOENIX_ALT_AUTH_HEADER="x-phoenix-api-key"

# 1) Lancer Phoenix sur 127.0.0.1:8899 (interne)
python3 -m phoenix.server.main --host 127.0.0.1 --port ${PHOENIX_INTERNAL_PORT} serve &

# 2) Lancer le proxy sur 0.0.0.0:8888 (port exposé Domino)
# Assure-toi d’avoir fastapi/uvicorn/httpx installés (pip)
uvicorn proxy:app --host 0.0.0.0 --port 8888
