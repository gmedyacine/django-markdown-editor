import subprocess
import json
import redis

def get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace):
    # Construction de la commande curl
    curl_command = [
        "curl", "-s",  # "-s" pour "silent"
        "-X", "GET",
        f"{vault_url}/v1/{secret_path}",
        "-H", f"X-Vault-Token: {vault_token}",
        "-H", "Accept: application/json",
        "-H", f"X-Vault-Namespace: {vault_namespace}"
    ]

    # Exécution de la commande curl
    result = subprocess.run(curl_command, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)  # Conversion de la réponse JSON en dictionnaire Python
    else:
        raise Exception("Failed to retrieve secret: " + result.stderr)

def test_redis_connectivity(redis_host, redis_port, redis_user, redis_password):
    # Connexion à Redis
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        username=redis_user,
        password=redis_password,
        decode_responses=True
    )
    
    try:
        # Test de connectivité via PING
        response = r.ping()
        if response:
            print("Successfully connected to Redis")
        else:
            print("Failed to connect to Redis")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")

# Exemple d'utilisation
vault_url = "https://vault.staging.echonet.com"
vault_token = "votre_token_vault"
vault_namespace = "UPM_CARDIF/8785/EC002102860"
secret_path = "cloud/data/redis/RDO021000358"
redis_host = "redis_host_address"  # Remplacez par l'adresse de votre serveur Redis
redis_port = 6379  # Le port Redis par défaut est 6379

try:
    # Récupération des secrets depuis Vault
    secret_data = get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace)
    
    # Extraction du mot de passe et de l'utilisateur Redis depuis la réponse JSON
    redis_user = secret_data['data']['data']['user']
    redis_password = secret_data['data']['data']['password']
    
    # Test de la connectivité à Redis
    test_redis_connectivity(redis_host, redis_port, redis_user, redis_password)

except Exception as e:
    print(str(e))
