import requests
import base64

def get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace):
    # Construction de l'URL de l'API
    url = f"{vault_url}/v1/{secret_path}"

    # Construction des headers pour l'authentification et les options d'API
    headers = {
        "X-Vault-Token": vault_token,
        "Accept": "application/json",
        "X-Vault-Namespace": vault_namespace
    }

    # Exécution de la requête GET via requests
    response = requests.get(url, headers=headers)

    # Vérification de la réponse
    if response.status_code == 200:
        return response.json()  # Conversion de la réponse JSON en dictionnaire Python
    else:
        raise Exception(f"Failed to retrieve secret: {response.status_code} {response.text}")

# Exemple d'utilisation pour récupérer le certificat
vault_url = "https://vault.staging.echonet.com"
vault_token = "votre_token_vault"
vault_namespace = "UPM_CARDIF/8785/EC002102860"
secret_path = "cloud/data/redis/RDO021000358"

try:
    secret_data = get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace)
    
    # Récupérer le certificat encodé en Base64
    certificate_base64 = secret_data['data']['data']['certificate']
    
    # Décodage du certificat Base64 en binaire
    certificate_decoded = base64.b64decode(certificate_base64)

    # Ajouter les balises BEGIN et END autour du certificat
    pem_certificate = f"-----BEGIN CERTIFICATE-----\n{certificate_base64}\n-----END CERTIFICATE-----"

    # Sauvegarder le certificat décodé dans un fichier
    with open("/tmp/redis_certificate.pem", "w") as cert_file:
        cert_file.write(pem_certificate)

    print("Certificat décodé et sauvegardé dans /tmp/redis_certificate.pem")

except Exception as e:
    print(str(e))
