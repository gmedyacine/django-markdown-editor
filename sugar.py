import os
import json
import requests

SESAME_URL = os.getenv(
    "SESAME_URL",
    "https://europe-sesame-services-uatprj-assurance.staging.echonet/sesame_services/services/Authentica"
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
        raise RuntimeError("SESAME_UID / SESAME_PASSWORD manquants dans l'environnement Domino.")

    soap_envelope = build_soap_envelope(SESAME_UID, SESAME_PASSWORD)

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "Accept": "*/*",
        "Connection": "close",
        "User-Agent": "curl/7.87.0",  # pour coller à ton curl
        # Si jamais ils demandent un SOAPAction, tu l'ajoutes ici
        # "SOAPAction": "loginInUserRef",
    }

    print("=== REQUÊTE ENVOYÉE ===")
    print("URL:", SESAME_URL)
    print("Headers:", json.dumps(headers, indent=2))
    print("Body SOAP (tronqué):")
    print(soap_envelope[:600], "...\n")

    # Je désactive la vérif SSL pour ce POC, tu pourras remettre un CA plus tard
    try:
        resp = requests.post(
            SESAME_URL,
            headers=headers,
            data=soap_envelope,
            timeout=30,
            verify=False,
            allow_redirects=False,  # IMPORTANT pour voir clairement le 302
        )
    except Exception as e:
        print("❌ Erreur réseau:", repr(e))
        return None

    print("=== RÉPONSE BRUTE ===")
    print("Status HTTP:", resp.status_code)
    print("Headers:", json.dumps(dict(resp.headers), indent=2, ensure_ascii=False))
    print("Body (tronqué):")
    print(resp.text[:4000])

    # Si c'est une redirection, on le montre clairement
    if 300 <= resp.status_code < 400:
        print("\n⚠️ Le serveur renvoie une REDIRECTION (", resp.status_code, ").")
        print("Location:", resp.headers.get("Location"))

    return resp


if __name__ == "__main__":
    call_sesame_auth()
