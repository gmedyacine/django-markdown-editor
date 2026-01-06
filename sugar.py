import os
import json
import re
import requests
import xmltodict


# ====== ENV ======
SESAME_URL = os.getenv(
    "SESAME_URL",
    "https://europe-sesame-services-uatprj-assurance.staging.echonet/sesame_services/services/AuthenticationServicesWSP",
)
SESAME_UID = os.getenv("SESAME_UID")
SESAME_PASSWORD = os.getenv("SESAME_PASSWORD")

DOC_ID = os.getenv("DOC_ID", "255ce394-c033-4b8e-a7b4-0ee93d2b958a")

SUGAR_BASE_URL = os.getenv("SUGAR_BASE_URL", "https://sugar-services.europe-staging.echonet")
SUGAR_BS = os.getenv("SUGAR_BS", "dc-docper-bm")
CARDIF_CONSUMER = os.getenv("CARDIF_CONSUMER", "SUGAR")
OUT_DIR = os.getenv("OUT_DIR", ".")
VERIFY_SSL = os.getenv("VERIFY_SSL", "false").lower() in ("1", "true", "yes")

# Permet d’ajouter des headers du curl sans recoder :
# ex: export SUGAR_EXTRA_HEADERS_JSON='{"X-FOO":"bar","x-user-id":"123"}'
SUGAR_EXTRA_HEADERS_JSON = os.getenv("SUGAR_EXTRA_HEADERS_JSON", "")


# ====== SOAP (SESAME) ======
def build_soap_envelope(uid: str, password: str, auth_type: str = "GROUP") -> str:
    # (tu peux adapter les namespaces si besoin)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:sprox="http://proxy.standard.services.sesame.bnppa.com">
  <soapenv:Header/>
  <soapenv:Body>
    <sprox:loginInUserRef>
      <login>{uid}</login>
      <password>{password}</password>
      <authType>{auth_type}</authType>
    </sprox:loginInUserRef>
  </soapenv:Body>
</soapenv:Envelope>
"""


def _pick(d: dict, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return None


def parse_token_from_soap(xml_text: str) -> str:
    obj = xmltodict.parse(xml_text)

    env = _pick(obj, "SOAP-ENV:Envelope", "soapenv:Envelope", "Envelope")
    if not env:
        raise RuntimeError("SOAP: Envelope introuvable")

    body = _pick(env, "SOAP-ENV:Body", "soapenv:Body", "Body")
    if not body:
        raise RuntimeError("SOAP: Body introuvable")

    # La réponse peut être ns3:loginInUserRefResponse, etc. => on cherche une clé qui finit par loginInUserRefResponse
    resp_key = None
    for k in body.keys():
        if str(k).endswith("loginInUserRefResponse"):
            resp_key = k
            break

    if not resp_key:
        raise RuntimeError(f"SOAP: loginInUserRefResponse introuvable. Clés Body={list(body.keys())}")

    resp_obj = body[resp_key]

    # Pareil, la clé token peut être loginInUserRefReturn (souvent sans namespace)
    token = None
    for k, v in resp_obj.items():
        if str(k).endswith("loginInUserRefReturn"):
            token = v
            break

    if not token:
        raise RuntimeError(f"SOAP: loginInUserRefReturn introuvable. Clés={list(resp_obj.keys())}")

    return str(token)


def call_sesame_auth() -> str:
    if not SESAME_UID or not SESAME_PASSWORD:
        raise RuntimeError("SESAME_UID / SESAME_PASSWORD manquants dans l'environnement.")

    soap_envelope = build_soap_envelope(SESAME_UID, SESAME_PASSWORD)

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "Accept": "*/*",
        "Connection": "close",
        "User-Agent": "curl/7.87.0",  # pour coller à ton curl
        # Si un jour ils demandent un SOAPAction, tu l'ajoutes ici :
        # "SOAPAction": "loginInUserRef",
    }

    print("=== REQUÊTE SESAME (SOAP) ===")
    print("URL:", SESAME_URL)
    print("Headers:", json.dumps(headers, indent=2))

    resp = requests.post(
        SESAME_URL,
        headers=headers,
        data=soap_envelope,
        timeout=50,
        verify=VERIFY_SSL,
        allow_redirects=False,
    )

    print("=== RÉPONSE SESAME ===")
    print("HTTP:", resp.status_code)
    print("Headers:", json.dumps(dict(resp.headers), indent=2, ensure_ascii=False))
    print("Body (début):", resp.text[:400])

    if 300 <= resp.status_code < 400:
        raise RuntimeError(f"SESAME: Redirection {resp.status_code} vers {resp.headers.get('Location')}")

    resp.raise_for_status()

    token = parse_token_from_soap(resp.text)
    return token


# ====== SUGAR (équivalent curl GET) ======
def _content_disposition_filename(cd: str) -> str | None:
    if not cd:
        return None
    # ex: attachment; filename="xxx.pdf"
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, flags=re.IGNORECASE)
    return m.group(1) if m else None


def download_document(token: str, doc_id: str) -> str:
    token = token.strip()
    print("TOKEN repr =", repr(token))
    print("TOKEN len  =", len(token))

    url = f"{SUGAR_BASE_URL}/sugar-backend-webapp/arender/document/{doc_id}/file"

    headers = {
        "Accept": "application/octet-stream",
        "X-SUGAR-BS": SUGAR_BS,
        "X-CARDIF-CONSUMER": CARDIF_CONSUMER,
        "X-CARDIF-AUTH-TOKEN": token,
        "Accept-Encoding": "identity",
        "Connection": "close",
        "User-Agent": "curl/7.87.0",
    }

    s = requests.Session()
    s.trust_env = False  # IMPORTANT : ignore HTTP(S)_PROXY / NO_PROXY etc.

    resp = s.get(
        url,
        headers=headers,
        timeout=80,
        verify=VERIFY_SSL,
        allow_redirects=False,
        stream=True,
    )

    # Vérifie ce qui est VRAIMENT parti sur le wire
    print("=== HEADERS ENVOYÉS (requests) ===")
    print(json.dumps(dict(resp.request.headers), indent=2, ensure_ascii=False))

    print("HTTP:", resp.status_code)
    if resp.status_code != 200:
        # le 401 a souvent un body JSON utile
        try:
            print("Body (401/err):", resp.text[:2000])
        except Exception:
            print("Body (401/err): <non lisible>")
        resp.raise_for_status()

    os.makedirs(OUT_DIR, exist_ok=True)

    cd = resp.headers.get("Content-Disposition", "")
    filename = f"{doc_id}.bin"
    if "filename=" in cd:
        filename = cd.split("filename=")[-1].strip().strip('"')

    out_path = os.path.join(OUT_DIR, filename)

    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)

    print("✅ téléchargé:", out_path)
    return out_path


def main():
    token = call_sesame_auth()
    print("✅ Token récupéré (début):", token[:20], "...")
    download_document(token, DOC_ID)


if __name__ == "__main__":
    main()
