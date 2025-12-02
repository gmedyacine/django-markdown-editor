import os
import json
import requests
import xml.etree.ElementTree as ET


# === Paramètres pris dans l'environnement Domino ===
# À définir dans les "Environment Variables" du workspace / projet Domino
SESAME_URL = os.getenv(
    "SESAME_URL",
    "https://europe-sesame-services-uatprj-assurance.staging.echonet/sesame_services/services/Authentica"  # <-- adapte si l'URL est un peu différente
)
SESAME_UID = os.getenv("SESAME_UID")          # ton UID annuaire
SESAME_PASSWORD = os.getenv("SESAME_PASSWORD")  # ton mot de passe annuaire

# Optionnel : si un jour on doit remettre ce header
CARDIF_AUTH_TOKEN = os.getenv("CARDIF_AUTH_TOKEN")  # sinon None


def build_soap_envelope(uid: str, password: str, auth_type: str = "GROUP") -> str:
    """
    Construit l'enveloppe SOAP exactement comme dans ton curl.
    """
    return f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:prox="http://proxy.standard.services.sesame.bnppa.com">
   <soapenv:Header/>
   <soapenv:Body>
      <prox:loginInUserRef>
         <login>{uid}</login>
         <password>{password}</password>
         <authType>{auth_type}</authType>
      </prox:loginInUserRef>
   </soapenv:Body>
</soapenv:Envelope>"""


def extract_token_from_response(xml_body: str) -> str | None:
    """
    Essaie de récupérer le token dans la réponse SOAP.
    ATTENTION : il faut mettre le bon nom de tag (token, sessionId, etc.).
    """
    try:
        root = ET.fromstring(xml_body)
    except ET.ParseError:
        return None

    ns = {
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "prox": "http://proxy.standard.services.sesame.bnppa.com",
    }

    # À ADAPTER : si la réponse ressemble à <prox:token>...</prox:token>
    # change './/prox:token' si le nom du tag est différent (ex: sessionId, sesameToken, etc.)
    token_elt = root.find(".//prox:token", ns)
    if token_elt is not None and token_elt.text:
        return token_elt.text.strip()

    return None


def call_sesame_auth() -> dict:
    """
    Appelle SESAME Europe pour récupérer un token.
    Retourne un dict avec tous les détails de la réponse.
    """
    if not SESAME_UID or not SESAME_PASSWORD:
        raise RuntimeError(
            "SESAME_UID et/ou SESAME_PASSWORD ne sont pas définis dans l'environnement."
        )

    soap_envelope = build_soap_envelope(SESAME_UID, SESAME_PASSWORD)

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
    }

    # D'après la discussion, le header X-CARDIF-AUTH-TOKEN n'est PAS nécessaire
    # pour récupérer le token. On le garde en option si jamais :
    if CARDIF_AUTH_TOKEN:
        headers["X-CARDIF-AUTH-TOKEN"] = CARDIF_AUTH_TOKEN

    response = requests.post(
        SESAME_URL,
        headers=headers,
        data=soap_envelope,
        timeout=30,
        # verify=False  # à activer seulement si vous avez un souci de certificat interne
    )

    # Récupération du token dans la réponse SOAP
    token = None
    try:
        token = extract_token_from_response(response.text)
    except Exception:
        # on laisse passer, on aura déjà le body complet pour debug
        pass

    # Construction d'un retour détaillé
    result = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.text,
        "token": token,
    }

    # Affichage "verbeux" dans les logs du workspace
    print("=== SESAME Europe – Auth ===")
    print(f"URL           : {SESAME_URL}")
    print(f"HTTP status   : {response.status_code}")
    print()
    print("=== Headers de réponse ===")
    print(json.dumps(result["headers"], indent=2, ensure_ascii=False))
    print()
    print("=== Body brut ===")
    print(result["body"])
    print()
    print("=== Token extrait ===")
    print(token if token else "⚠️ Aucun token trouvé (adapter le parseur XML).")

    return result


if __name__ == "__main__":
    call_sesame_auth()
