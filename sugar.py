import os
import json
import requests
import xml.etree.ElementTree as ET

SESAME_URL = os.getenv(
    "SESAME_URL",
    "https://europe-sesame-services-uatprj-assurance.staging.echonet/sesame_services/services/Authentica"  # adapte exactement à ton curl
)
SESAME_UID = os.getenv("SESAME_UID")
SESAME_PASSWORD = os.getenv("SESAME_PASSWORD")

def build_soap_envelope(uid: str, password: str, auth_type: str = "GROUP") -> str:
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


def call_sesame_auth():
    if not SESAME_UID or not SESAME_PASSWORD:
        raise RuntimeError("SESAME_UID / SESAME_PASSWORD manquants dans l'environnement.")

    soap_envelope = build_soap_envelope(SESAME_UID, SESAME_PASSWORD)

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "Accept": "*/*",
        "Connection": "close",
        "User-Agent": "curl/7.87.0",  # on imite un curl classique
        # Ajoute ici d'autres headers si ton curl en a (SOAPAction, etc.)
    }

    print("=== REQUETE ENVoyee ===")
    print("URL:", SESAME_URL)
    print("Headers:", json.dumps(headers, indent=2))
    # évite d'afficher le mot de passe en clair si tu copies ça dans un ticket
    print("Body (tronqué):", soap_envelope[:500], "...\n")

    try:
        response = requests.post(
            SESAME_URL,
            headers=headers,
            data=soap_envelope,
            timeout=30,
            verify=False,  # pour l'instant, on reste en mode non vérifié
        )
    except requests.exceptions.ConnectionError as e:
        print("❌ ConnectionError vers SESAME (le serveur ferme la connexion sans répondre).")
        print(repr(e))
        return None
    except Exception as e:
        print("❌ Erreur inattendue:", repr(e))
        return None

    print("=== REPONSE ===")
    print("Status HTTP:", response.status_code)
    print("Headers:", json.dumps(dict(response.headers), indent=2, ensure_ascii=False))
    print("Body:", response.text[:4000])  # tronque un peu

    return response


if __name__ == "__main__":
    call_sesame_auth()
