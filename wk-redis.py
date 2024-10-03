import redis

# Remplacez ces valeurs par celles récupérées de Vault
redis_host = 'REDIS_HOST'  # Remplacez par l'adresse IP ou le nom de domaine de votre serveur Redis
redis_port = 6379  # Port par défaut de Redis, changez-le si votre configuration est différente
redis_user = 'USER_RETRIEVED_FROM_VAULT'
redis_password = 'PASSWORD_RETRIEVED_FROM_VAULT'

# Connexion à Redis
r = redis.Redis(host=redis_host, port=redis_port, username=redis_user, password=redis_password, decode_responses=True)

# Test de la connexion
try:
    response = r.ping()
    print("Redis is connected:", response)
except Exception as e:
    print("Failed to connect to Redis:", e)
