# ======= VAULT (mTLS + Namespace) =======
import os, requests, datetime as dt

VAULT_ADDR        = os.getenv("VAULT_ADDR")                         # https://hvault...:8200
VAULT_NAMESPACE   = os.getenv("VAULT_NAMESPACE")                    # ex: UPM_CARDIF/...
VAULT_KV_MOUNT    = os.getenv("VAULT_KV_MOUNT", "secret")           # "secret"
VAULT_SECRET_PATH = os.getenv("VAULT_SECRET_PATH", "domino-api/api-domino-run-jobs")

VAULT_CLIENT_CERT = os.getenv("VAULT_CLIENT_CERT")                  # PEM
VAULT_CLIENT_KEY  = os.getenv("VAULT_CLIENT_KEY")                   # PEM
VAULT_CACERT      = os.getenv("VAULT_CACERT")                       # CA chain; sinon vérifier par défaut
VAULT_INSECURE    = os.getenv("VAULT_INSECURE", "false").lower() == "true"

VERIFY = False if VAULT_INSECURE else (VAULT_CACERT if VAULT_CACERT else True)
CERT   = (VAULT_CLIENT_CERT, VAULT_CLIENT_KEY) if (VAULT_CLIENT_CERT and VAULT_CLIENT_KEY) else None
TIMEOUT = 20

def _h(token=None):
    h = {"Content-Type": "application/json", "X-Vault-Request": "true"}
    if VAULT_NAMESPACE:
        h["X-Vault-Namespace"] = VAULT_NAMESPACE
    if token:
        h["X-Vault-Token"] = token
    return h

def vault_login_cert(addr: str) -> str:
    """Login via auth/cert -> retourne client_token (utilisé ensuite pour read/write)."""
    if not CERT:
        raise RuntimeError("VAULT_CLIENT_CERT / VAULT_CLIENT_KEY manquants.")
    url = f"{addr.rstrip('/')}/v1/auth/cert/login"
    r = requests.post(url, headers=_h(), cert=CERT, verify=VERIFY, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["auth"]["client_token"]

# -------- Vérification d’accès (lecture) ----------
def verify_vault_read():
    """
    1) login cert -> token
    2) GET KV v2 (puis fallback v1) sur le secret demandé
    Affiche le diagnostic et renvoie True/False.
    """
    print(f"[CHECK] ns={VAULT_NAMESPACE or '(none)'}  mount={VAULT_KV_MOUNT}  path={VAULT_SECRET_PATH}")
    token = vault_login_cert(VAULT_ADDR)

    # Tentative KV v2
    url_v2 = f"{VAULT_ADDR.rstrip('/')}/v1/{VAULT_KV_MOUNT.strip('/')}/data/{VAULT_SECRET_PATH.strip('/')}"
    r = requests.get(url_v2, headers=_h(token), cert=CERT, verify=VERIFY, timeout=TIMEOUT)
    if r.status_code == 200:
        data = r.json().get("data", {}).get("data", {})
        version = r.json().get("data", {}).get("metadata", {}).get("version")
        print(f"[OK] KV v2 READ → version={version}  keys={list(data.keys())}")
        return True
    else:
        print(f"[INFO] KV v2 read → {r.status_code}: {r.text[:200]}")

    # Fallback KV v1
    url_v1 = f"{VAULT_ADDR.rstrip('/')}/v1/{VAULT_KV_MOUNT.strip('/')}/{VAULT_SECRET_PATH.strip('/')}"
    r2 = requests.get(url_v1, headers=_h(token), cert=CERT, verify=VERIFY, timeout=TIMEOUT)
    if r2.status_code == 200:
        print(f"[OK] KV v1 READ → keys={list((r2.json() or {}).keys())}")
        return True

    print(f"[FAIL] KV v1 read → {r2.status_code}: {r2.text[:200]}")
    print("      → si 403: vérifier policy du rôle cert et le namespace.")
    print("         KV v2 requis: path \"secret/data/domino-api/*\" { capabilities=[\"create\",\"update\",\"read\"] }")
    return False

# -------- Upsert de la clé api_domino_run_jobs (écriture) ----------
def upsert_api_domino_run_jobs(new_value: str, extra: dict | None = None):
    """
    - login cert -> client_token
    - lit (KV v2) puis fusionne la clé api_domino_run_jobs
    - écrit une nouvelle version (KV v2); fallback v1 si besoin
    """
    token = vault_login_cert(VAULT_ADDR)

    # 1) Lire existant (KV v2)
    current = {}
    url_read = f"{VAULT_ADDR.rstrip('/')}/v1/{VAULT_KV_MOUNT.strip('/')}/data/{VAULT_SECRET_PATH.strip('/')}"
    r = requests.get(url_read, headers=_h(token), cert=CERT, verify=VERIFY, timeout=TIMEOUT)
    if r.status_code == 200:
        current = (r.json().get("data") or {}).get("data") or {}
    elif r.status_code not in (404, 403):
        r.raise_for_status()  # autre erreur inattendue

    # 2) Fusion
    current["api_domino_run_jobs"] = new_value
    if extra and isinstance(extra, dict):
        current.update(extra)

    # 3) Write KV v2
    url_write_v2 = f"{VAULT_ADDR.rstrip('/')}/v1/{VAULT_KV_MOUNT.strip('/')}/data/{VAULT_SECRET_PATH.strip('/')}"
    r2 = requests.post(url_write_v2, headers=_h(token), json={"data": current},
                       cert=CERT, verify=VERIFY, timeout=TIMEOUT)
    if r2.status_code in (200, 204):
        ver = r2.json().get("data", {}).get("version")
        print(f"[OK] WRITE KV v2 → new version={ver}")
        return

    # 4) Fallback KV v1 (si le mount n’est finalement pas v2)
    if r2.status_code in (400, 404):
        url_write_v1 = f"{VAULT_ADDR.rstrip('/')}/v1/{VAULT_KV_MOUNT.strip('/')}/{VAULT_SECRET_PATH.strip('/')}"
        r3 = requests.post(url_write_v1, headers=_h(token), json=current,
                           cert=CERT, verify=VERIFY, timeout=TIMEOUT)
        r3.raise_for_status()
        print("[OK] WRITE KV v1")
        return

    raise RuntimeError(f"Vault write KV v2 failed [{r2.status_code}]: {r2.text[:300]}")
