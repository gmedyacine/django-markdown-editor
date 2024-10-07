import subprocess
import json
import redis

def get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace):
    """
    Fonction pour récupérer les secrets depuis Vault via un appel API avec curl.
    """
    # Construction de la commande curl
    curl_command = [
        "curl", "-s",  # "-s" pour "silent" afin de ne pas afficher les détails de la progression
        "-X", "GET",
        f"{vault_url}/v1/{secret_path}",  # URL complète pour l'appel API
        "-H", f"Authorization: Bearer {vault_token}",  # Utilisation du token pour l'authentification
        "-H", "Accept: application/json",  # Spécifier que nous attendons une réponse JSON
        "-H", f"X-Vault-Namespace: {vault_namespace}"  # Spécification du namespace
    ]

    # Exécution de la commande curl
    result = subprocess.run(curl_command, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)  # Conversion de la réponse JSON en dictionnaire Python
    else:
        raise Exception("Échec de la récupération des secrets : " + result.stderr)


def test_redis_connection(redis_host, redis_port, redis_user, redis_password):
    """
    Fonction pour tester la connexion à Redis en utilisant les informations récupérées.
    """
    try:
        # Connexion à Redis
        r = redis.Redis(host=redis_host, port=redis_port, username=redis_user, password=redis_password, decode_responses=True)
        # Envoyer une commande PING pour tester la connexion
        if r.ping():
            print("La connexion à Redis a réussi.")
        else:
            print("Échec de la connexion à Redis.")
    except Exception as e:
        print(f"Erreur lors de la connexion à Redis : {e}")


# Exemple d'utilisation
vault_url = "https://vault.staging.echonet.com"
vault_token = "votre_token_vault"
vault_namespace = "UPM_CARDIF/8785/EC002102860"
secret_path = "cloud/data/redis/RDO021000358"

try:
    # Récupération des informations depuis Vault
    secret_data = get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace)
    redis_password = secret_data['data']['data']['password']  # Ajustez le chemin selon la structure de votre réponse JSON
    redis_user = secret_data['data']['data']['user']
    print("Les informations ont été récupérées avec succès depuis Vault.")

    # Test de la connexion à Redis
    redis_host = "redis-host"  # Remplacez par l'adresse ou l'IP de votre serveur Redis
    redis_port = 6379  # Port par défaut de Redis, ajustez si nécessaire
    test_redis_connection(redis_host, redis_port, redis_user, redis_password)

except Exception as e:
    print(str(e))
