import os
import json
import re
import requests

DATASET_DIR = os.getenv("DATASET_DIR")           # OBLIGATOIRE
DATASET_SUBDIR = os.getenv("DATASET_SUBDIR", "") # optionnel

def _safe_filename(name: str) -> str:
    # empêche ../ et autres surprises
    name = (name or "").strip()
    name = os.path.basename(name)
    if not name:
        return "document.bin"
    # nettoyage soft
    name = re.sub(r"[^\w\-. ()]", "_", name)
    return name

def _build_output_path(filename: str) -> str:
    if not DATASET_DIR:
        raise RuntimeError("DATASET_DIR est obligatoire (chemin du dataset Domino).")

    out_dir = os.path.join(DATASET_DIR, DATASET_SUBDIR) if DATASET_SUBDIR else DATASET_DIR
    os.makedirs(out_dir, exist_ok=True)

    return os.path.join(out_dir, _safe_filename(filename))

def _auth_headers(token: str) -> dict:
    token = token.strip()
    return {
        "X-SUGAR-BS": SUGAR_BS,                 # IMPORTANT: dc-docpartners chez toi
        "X-CARDIF-CONSUMER": CARDIF_CONSUMER,   # SUGAR
        "X-CARDIF-AUTH-TOKEN": token,
        "Connection": "close",
        "User-Agent": "curl/7.87.0",
        "Accept-Encoding": "identity",
    }

def get_document_info(token: str, doc_id: str) -> dict:
    """
    Appel qui récupère les infos du doc (JSON) :
    - fileName
    - fileUri (souvent /arender/document/<id>/file)
    """
    url = f"{SUGAR_BASE_URL}/sugar-backend-webapp/arender/document/{doc_id}"
    headers = _auth_headers(token)
    headers["Accept"] = "application/json"

    s = requests.Session()
    s.trust_env = False  # évite proxies d'env

    resp = s.get(url, headers=headers, timeout=50, verify=VERIFY_SSL, allow_redirects=False)
    if resp.status_code != 200:
        print("HTTP:", resp.status_code)
        print("Body:", resp.text[:2000])
        resp.raise_for_status()

    data = resp.json()

    afd = data.get("arenderFileData", {}) if isinstance(data, dict) else {}
    file_name = (
        afd.get("fileName")
        or afd.get("documentFileName")
        or data.get("fileName")
        or f"{doc_id}.bin"
    )

    file_uri = (
        afd.get("fileUri")
        or afd.get("documentFileUri")
        or None
    )

    # fallback si l'API ne renvoie pas l'uri
    if not file_uri:
        file_uri = f"/sugar-backend-webapp/arender/document/{doc_id}/file"

    # construit une URL complète si besoin
    if file_uri.startswith("http"):
        download_url = file_uri
    else:
        download_url = f"{SUGAR_BASE_URL}{file_uri}"

    return {
        "doc_id": doc_id,
        "file_name": file_name,
        "download_url": download_url,
        "raw": data,
    }

def download_file(token: str, download_url: str, out_path: str) -> str:
    headers = _auth_headers(token)
    headers["Accept"] = "application/octet-stream"

    s = requests.Session()
    s.trust_env = False

    resp = s.get(
        download_url,
        headers=headers,
        timeout=80,
        verify=VERIFY_SSL,
        allow_redirects=False,
        stream=True,
    )

    if resp.status_code != 200:
        print("HTTP:", resp.status_code)
        try:
            print("Body:", resp.text[:2000])
        except Exception:
            pass
        resp.raise_for_status()

    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)

    print(f"✅ Sauvegardé: {out_path}")
    return out_path

def main():
    token = call_sesame_auth()

    info = get_document_info(token, DOC_ID)
    filename = info["file_name"]
    download_url = info["download_url"]

    out_path = _build_output_path(filename)
    download_file(token, download_url, out_path)

if __name__ == "__main__":
    main()
