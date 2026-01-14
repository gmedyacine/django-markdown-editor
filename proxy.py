# proxy.py
import os
import logging
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

# --- Configuration du Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] PROXY: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("proxy")

# --- Config ---
UPSTREAM = os.getenv("PHOENIX_UPSTREAM", "http://127.0.0.1:8899").rstrip("/")
ALT_HEADER = os.getenv("PHOENIX_ALT_AUTH_HEADER", "x-phoenix-api-key").lower()
FALLBACK_HEADER = "api_key"

app = FastAPI()

def _get_api_key(req: Request) -> str | None:
    h = req.headers
    return h.get(ALT_HEADER) or h.get(FALLBACK_HEADER)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    # 1. Log de la requête entrante
    logger.info(f"Incoming -> {request.method} /{path}")
    
    # Debug des headers (utile pour voir si Domino passe bien les infos)
    # logger.info(f"Headers reçus: {dict(request.headers)}")

    # 2. Construction de l'URL cible
    # Si path est vide, on tape la racine. Sinon on ajoute le path.
    url = f"{UPSTREAM}/{path}" if path else UPSTREAM
    
    # 3. Gestion du Body
    body = await request.body()

    # 4. Nettoyage et préparation des Headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # On force le host header vers le localhost interne pour éviter des erreurs de routing upstream
    headers["host"] = "127.0.0.1"

    # Gestion de l'Auth pour Phoenix
    api_key = _get_api_key(request)
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
        logger.info("-> API Key detected and injected as Bearer token")
    else:
        # Optionnel: Logger si pas de clé (pour comprendre pourquoi on est rejeté)
        logger.debug("-> No API Key found in headers")

    # 5. Forward vers Phoenix
    async with httpx.AsyncClient(verify=False, timeout=60.0, follow_redirects=True) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                params=dict(request.query_params),
                headers=headers,
                content=body,
            )
        except Exception as e:
            logger.error(f"Upstream Error: {e}")
            return Response(content=f"Proxy Error: {str(e)}", status_code=502)

    # 6. Filtrage des headers de réponse (important pour éviter les erreurs de compression)
    excluded = {"transfer-encoding", "connection", "content-encoding", "content-length"}
    out_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

    logger.info(f"Upstream responded: {resp.status_code} for /{path}")

    return Response(content=resp.content, status_code=resp.status_code, headers=out_headers)
