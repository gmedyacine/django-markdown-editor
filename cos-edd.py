# =====================  VAULT (mTLS) =====================
import os, requests, datetime as dt

VAULT_ADDR            = os.getenv("VAULT_ADDR")                   # ex: https://vault.company:8200
VAULT_KV_MOUNT        = os.getenv("VAULT_KV_MOUNT", "secret")     # ton mount KV (v2 par défaut)
VAULT_SECRET_PATH     = os.getenv("VAULT_SECRET_PATH",            # chemin logique SANS "data/"
                                 f"domino/service-accounts/{sa_id}")
VAULT_CERT            = os.getenv("VAULT_CLIENT_CERT")            # chemin .pem du cert client
VAULT_KEY             = os.getenv("VAULT_CLIENT_KEY")             # chemin .pem de la clé privée
VAULT_CACERT          = os.getenv("VAULT_CACERT")                 # CA bundle/CRT pour vérifier Vault
VAULT_CERT_AUTH_NAME  = os.getenv("VAULT_CERT_AUTH_NAME")         # optionnel (nom du rôle cert)
VERIFY = VAULT_CACERT if VAULT_CACERT else True
CERT = (VAULT_CERT, VAULT_KEY) if (VAULT_CERT and VAULT_KEY) else None
TIMEOUT = 20

def vault_login_cert(addr, cert=CERT, verify=VERIFY, name=VAULT_CERT_AUTH_NAME):
    """Auth cert → retourne un client_token Vault."""
    if not cert:
        raise RuntimeError("Cert mTLS manquant (VAULT_CLIENT_CERT / VAULT_CLIENT_KEY).")
    url = f"{addr.rstrip('/')}/v1/auth/cert/login"
    payload = {"name": name} if name else None
    r = requests.post(url, json=payload, cert=cert, verify=verify, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["auth"]["client_token"]

def vault_write_kv(addr, token, mount, path, data, verify=VERIFY):
    """Écrit en KV v2 (/data/...), fallback KV v1 si 400/404."""
    h = {"X-Vault-Token": token, "Content-Type": "application/json"}
    # KV v2
    url_v2 = f"{addr.rstrip('/')}/v1/{mount.strip('/')}/data/{path.strip('/')}"
    r = requests.post(url_v2, headers=h, json={"data": data}, verify=verify, timeout=TIMEOUT)
    if r.status_code in (200, 204):
        return "kv2"
    if r.status_code in (400, 404):
        # KV v1
        url_v1 = f"{addr.rstrip('/')}/v1/{mount.strip('/')}/{path.strip('/')}"
        r2 = requests.post(url_v1, headers=h, json=data, verify=verify, timeout=TIMEOUT)
        r2.raise_for_status()
        return "kv1"
    r.raise_for_status()
    return "kv2"

def push_to_vault(token_value, token_name, sa_id, sa_email=None, sa_name=None):
    if not VAULT_ADDR:
        raise RuntimeError("VAULT_ADDR non défini.")
    # 1) login cert → client_token
    client_token = vault_login_cert(VAULT_ADDR)
    # 2) payload
    payload = {
        "token": token_value,
        "token_name": token_name,
        "service_account_id": sa_id,
        "service_account_email": sa_email,
        "service_account_name": sa_name,
        "rotated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        # Domino ≈ 3 mois → simple indication
        "expires_hint": (dt.datetime.utcnow() + dt.timedelta(days=90)).replace(microsecond=0).isoformat() + "Z",
        "source": "domino-rotate-script",
    }
    # 3) write
    mode = vault_write_kv(VAULT_ADDR, client_token, VAULT_KV_MOUNT, VAULT_SECRET_PATH, payload)
    print(f"[OK] Token Domino poussé dans Vault ({mode}) → {VAULT_KV_MOUNT}/{VAULT_SECRET_PATH}")
# =========================================================
