# ---------- VAULT (mTLS + KV v2 + Namespace) ----------
import os, requests, datetime as dt

VAULT_ADDR        = os.getenv("VAULT_ADDR")                         # https://hvault.staging.echonet:8200
VAULT_NAMESPACE   = os.getenv("VAULT_NAMESPACE")                    # ex: UPM_CARDIF/BF05/EC002I002860
VAULT_KV_MOUNT    = os.getenv("VAULT_KV_MOUNT", "secret")           # "secret"
VAULT_SECRET_PATH = os.getenv("VAULT_SECRET_PATH",                  # "domino-api/api-domino-run-jobs"
                              "domino-api/api-domino-run-jobs")

VAULT_CLIENT_CERT = os.getenv("VAULT_CLIENT_CERT")                  # PEM
VAULT_CLIENT_KEY  = os.getenv("VAULT_CLIENT_KEY")                   # PEM
VAULT_CACERT      = os.getenv("VAULT_CACERT")                       # CA chain (recommandé)

VERIFY = VAULT_CACERT if VAULT_CACERT else True
CERT   = (VAULT_CLIENT_CERT, VAULT_CLIENT_KEY) if (VAULT_CLIENT_CERT and VAULT_CLIENT_KEY) else None
TIMEOUT = 20

def _headers(token=None):
    h = {"Content-Type": "application/json", "X-Vault-Request": "true"}
    if VAULT_NAMESPACE:
        h["X-Vault-Namespace"] = VAULT_NAMESPACE
    if token:
        h["X-Vault-Token"] = token
    return h

def vault_login_cert(addr: str) -> str:
    """Auth cert → récupère un client_token Vault (namespace inclus)."""
    if not CERT:
        raise RuntimeError("mTLS requis: VAULT_CLIENT_CERT et VAULT_CLIENT_KEY manquants.")
    url = f"{addr.rstrip('/')}/v1/auth/cert/login"
    r = requests.post(url, headers=_headers(), cert=CERT, verify=VERIFY, timeout=TIMEOUT)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"Vault cert login failed [{r.status_code}]: {r.text}") from e
    j = r.json()
    return j["auth"]["client_token"]

def vault_write_kv(addr: str, token: str, mount: str, path: str, data: dict, verify=VERIFY):
    """
    Écriture KV v2: POST /v1/<mount>/data/<path> avec body {"data": {...}}
    Fallback KV v1 si 400/404 (rare en l'état vu ton UI).
    """
    # KV v2
    url_v2 = f"{addr.rstrip('/')}/v1/{mount.strip('/')}/data/{path.strip('/')}"
    r = requests.post(url_v2, headers=_headers(token), json={"data": data},
                      cert=CERT, verify=verify, timeout=TIMEOUT)
    if r.status_code in (200, 204):
        return "kv2"
    if r.status_code in (400, 404):
        # Fallback KV v1 si jamais le mount est en v1
        url_v1 = f"{addr.rstrip('/')}/v1/{mount.strip('/')}/{path.strip('/')}"
        r2 = requests.post(url_v1, headers=_headers(token), json=data,
                           cert=CERT, verify=verify, timeout=TIMEOUT)
        try:
            r2.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"Vault write KV v1 failed [{r2.status_code}]: {r2.text}") from e
        return "kv1"
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"Vault write KV v2 failed [{r.status_code}]: {r.text}") from e

def push_to_vault(token_value: str, token_name: str, sa_id: str, sa_email: str = None, sa_name: str = None):
    """Pousse UNE NOUVELLE VERSION de la clé 'api_domino_run_jobs' dans secret/domino-api/api-domino-run-jobs."""
    if not VAULT_ADDR:
        raise RuntimeError("VAULT_ADDR non défini.")
    client_token = vault_login_cert(VAULT_ADDR)

    # Tu voulais uniquement cette clé-là (le reste est optionnel)
    payload = {
        "api_domino_run_jobs": token_value,
        # --- si tu veux garder du contexte en plus, décommente :
        # "meta": {
        #   "token_name": token_name,
        #   "service_account_id": sa_id,
        #   "service_account_email": sa_email,
        #   "service_account_name": sa_name,
        #   "rotated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        #   "expires_hint": (dt.datetime.utcnow() + dt.timedelta(days=90)).replace(microsecond=0).isoformat() + "Z",
        # }
    }

    mode = vault_write_kv(VAULT_ADDR, client_token, VAULT_KV_MOUNT, VAULT_SECRET_PATH, payload)
    print(f"[OK] Nouvelle version écrite ({mode}) → {VAULT_KV_MOUNT}/{VAULT_SECRET_PATH}")
# --------------------------------------------------------------
