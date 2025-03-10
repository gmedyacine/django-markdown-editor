import os
import base64
import requests
import ibm_boto3
from ibm_botocore.client import Config, ClientError

# Configuration pour Vault
VAULT_URL = "https://hvault.staging.echonet"
VAULT_SECRET_PATH = "/v1/UPM_CARDIF/8705/EC002I002860/objsto/kv/co002i005676"
VAULT_TOKEN = os.getenv("VAULT_TOKEN")  # Le token Vault doit être passé en variable d'environnement

def get_secrets_from_vault():
    headers = {
        "X-Vault-Token": VAULT_TOKEN
    }
    response = requests.get(f"{VAULT_URL}{VAULT_SECRET_PATH}", headers=headers)
    
    if response.status_code == 200:
        secrets = response.json()["data"]["data"]
        return {
            "COS_HMAC_ACCESS_KEY_ID": secrets["cos_hmac_keys_access_key_id"],
            "COS_HMAC_SECRET_ACCESS_KEY": secrets["cos_hmac_keys_secret_access_key"],
            "COS_ENDPOINT": "https://bu0021009393.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4229",
            "BUCKET_NAME": "bu0021009393"
        }
    else:
        raise Exception(f"Failed to retrieve secrets from Vault: {response.status_code} - {response.text}")

# Récupérer les secrets et les utiliser pour configurer la connexion à IBM COS
try:
    secrets = get_secrets_from_vault()
    cos_client = ibm_boto3.client(
        "s3",
        aws_access_key_id=secrets["COS_HMAC_ACCESS_KEY_ID"],
        aws_secret_access_key=secrets["COS_HMAC_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        endpoint_url=secrets["COS_ENDPOINT"]
    )

    def create_text_file(bucket_name, item_name, file_text):
        print(f"Creating new item: {item_name} in bucket: {bucket_name}")
        try:
            cos_client.put_object(
                Bucket=bucket_name,
                Key=item_name,
                Body=file_text
            )
            print(f"Item: {item_name} created successfully!")
        except ClientError as e:
            print(f"CLIENT ERROR: {e}")
        except Exception as e:
            print(f"Failed to create text file: {e}")

    # Exemple de création de fichier
    create_text_file(secrets["BUCKET_NAME"], "example.txt", "This is a test file.")

except Exception as e:
    print(f"Error: {e}")

import os
import ibm_boto3
from ibm_botocore.client import Config

# Paramètres d’exemple
HMAC_ACCESS_KEY_ID = "VOTRE_ACCESS_KEY"
HMAC_SECRET_ACCESS_KEY = "VOTRE_SECRET_KEY"
ENDPOINT_URL = "https://s3.eu-fr2.cloud-object-storage.appdomain.cloud"
BUCKET_NAME = "votre_bucket"
OBJECT_KEY = "nom-de-fichier-dans-le-bucket.txt"
LOCAL_PATH = "/data/nom-de-fichier-local.txt"  # Chemin local où vous voulez télécharger

# Création du client S3
cos_client = ibm_boto3.client(
    "s3",
    aws_access_key_id=HMAC_ACCESS_KEY_ID,
    aws_secret_access_key=HMAC_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    endpoint_url=ENDPOINT_URL
)

def download_single_file_with_timing():
    """Télécharge un fichier depuis IBM COS et mesure le temps écoulé."""
    os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)
    
    try:
        start_time = time.time()
        
        cos_client.download_file(BUCKET_NAME, OBJECT_KEY, LOCAL_PATH)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"Fichier '{OBJECT_KEY}' téléchargé avec succès dans '{LOCAL_PATH}'.")
        print(f"Temps de téléchargement : {elapsed:.2f} secondes.")
        
        # Si vous voulez calculer le débit, vous pouvez mesurer la taille du fichier local
        file_size_bytes = os.path.getsize(LOCAL_PATH)
        mb_size = file_size_bytes / (1024 * 1024)
        print(f"Taille du fichier : {mb_size:.2f} MB")
        if elapsed > 0:
            throughput = mb_size / elapsed
            print(f"Débit approx. : {throughput:.2f} MB/s")
        
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")

# Appel de la fonction
download_single_file()
