import requests
import redis
import json
import os

# Configuration des variables d'environnement ou remplacer par des valeurs statiques sécurisées
VAULT_ADDR = os.getenv('VAULT_ADDR', 'https://vault.staging.echonen.com')
VAULT_TOKEN = os.getenv('VAULT_TOKEN', 'your-vault-token')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-host')

def get_redis_credentials(vault_url, vault_token):
    """Récupère les identifiants Redis depuis Vault."""
    headers = {'X-Vault-Token': vault_token}
    user_path = f"{vault_url}/v1/UPM_CARDIF/8785/EC002102860/cloud/data/redis/RDO021000358"
    pass_path = f"{vault_url}/v1/UPM_CARDIF/8785/EC002102860/cloud/data/redis/RDO021000358"

    # Récupération du nom d'utilisateur
    response = requests.get(user_path, headers=headers)
    redis_user = json.loads(response.text)['data']['data']['user']

    # Récupération du mot de passe
    response = requests.get(pass_path, headers=headers)
    redis_password = json.loads(response.text)['data']['data']['password']

    return redis_user, redis_password

def test_redis_connection(redis_host, redis_user, redis_password):
    """Teste la connexion à Redis."""
    try:
        r = redis.Redis(host=redis_host, username=redis_user, password=redis_password, decode_responses=True)
        ping_response = r.ping()
        print("Redis is connected:", ping_response)
    except Exception as e:
        print("Failed to connect to Redis:", e)

def main():
    redis_user, redis_password = get_redis_credentials(VAULT_ADDR, VAULT_TOKEN)
    test_redis_connection(REDIS_HOST, redis_user, redis_password)

if __name__ == "__main__":
    main()
