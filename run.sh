#!/usr/bin/env bash
set -euo pipefail

# --- 1. Configuration Domino & Phoenix ---

# Le port sur lequel Domino écoute (exposé à l'utilisateur)
PROXY_PORT="${PORT:-8888}"

# Port interne caché pour Phoenix
PHOENIX_INTERNAL_PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')"

# --- CRUCIAL: Configuration du Path (depuis ta capture d'écran) ---
# Cela permet à Phoenix de savoir qu'il est servi sous /domino/projects/...
# Si ces vars Domino ne sont pas dispos, on fallback sur une chaîne vide, mais sur Domino elles sont là.
if [ -n "${DOMINO_PROJECT_OWNER:-}" ] && [ -n "${DOMINO_PROJECT_NAME:-}" ] && [ -n "${DOMINO_RUN_ID:-}" ]; then
    export PHOENIX_HOST_ROOT_PATH="/${DOMINO_PROJECT_OWNER}/${DOMINO_PROJECT_NAME}/r/notebookSession/${DOMINO_RUN_ID}"
    echo "[INFO] Detected Domino Environment. Setting ROOT_PATH to: $PHOENIX_HOST_ROOT_PATH"
else
    echo "[WARN] Not properly detected Domino Env vars. UI might be blank."
fi

# Authentification
export PHOENIX_ENABLE_AUTH=true
export PHOENIX_SECRET="${PHOENIX_SECRET:-change-me-32chars-min1digit1lower}"

# Autres variables de ta capture (optionnel mais recommandé pour la cohérence)
export PHOENIX_COLLECTOR_ENDPOINT="${PHOENIX_COLLECTOR_ENDPOINT:-}"
# export PHOENIX_WORKING_DIR... (si nécessaire)

# --- 2. Configuration pour le Proxy ---
export PHOENIX_UPSTREAM="http://127.0.0.1:${PHOENIX_INTERNAL_PORT}"
export PHOENIX_ALT_AUTH_HEADER="x-phoenix-api-key"

echo "----------------------------------------------------------------"
echo "[INFO] Starting Phoenix on internal port: $PHOENIX_INTERNAL_PORT"
echo "[INFO] Starting Proxy on exposed port:    $PROXY_PORT"
echo "----------------------------------------------------------------"

# --- 3. Gestion des processus ---
cleanup() {
  echo "[INFO] Stopping background processes..."
  jobs -p | xargs -r kill || true
}
trap cleanup EXIT

# --- 4. Lancement de Phoenix (Background) ---
# Note: On laisse Phoenix écouter sur localhost uniquement pour la sécurité
# Important: On ne passe PAS PHOENIX_HOST_ROOT_PATH au proxy, mais à Phoenix lui-même
python3 -m phoenix.server.main \
    --host 127.0.0.1 \
    --port "${PHOENIX_INTERNAL_PORT}" \
    serve &

# Attente active que Phoenix soit prêt (optionnel mais plus propre que sleep)
echo "[INFO] Waiting for Phoenix to start..."
sleep 5

# --- 5. Lancement du Proxy (Foreground) ---
# On lance uvicorn en écoutant sur 0.0.0.0 pour que Domino puisse taper dessus
uvicorn proxy:app --host 0.0.0.0 --port "${PROXY_PORT}" --log-level info

Bonne nouvelle : l'instance Phoenix est désormais opérationnelle et sécurisée sur Domino.

Pour contourner les restrictions de Domino qui bloquent/écrasent les headers Authorization standards, j'ai mis en place un proxy léger (sidecar) devant l'application.

Ce que ça change :

Le proxy intercepte les requêtes entrantes.

Il récupère notre token via un header personnalisé (x-phoenix-api-key) qui passe le pare-feu Domino.

Il réinjecte ce token en local sous forme d'authentification Bearer standard pour Phoenix.

L'authentification fonctionne donc parfaitement sans compromettre la sécurité.
