import ibm_boto3
from ibm_botocore.client import Config, ClientError

# Configuration des informations d'authentification via HMAC
COS_ENDPOINT = "https://bu0021009393.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4229"  # Ton endpoint direct
COS_HMAC_ACCESS_KEY_ID = "8cac968e8be4775a706551937d1bd1a"  # Clé d'accès HMAC
COS_HMAC_SECRET_ACCESS_KEY = "9bdadc074ae7ae587e4df4..."  # Clé secrète HMAC

# Création du client IBM COS en utilisant HMAC
cos_client = ibm_boto3.client(
    "s3",
    aws_access_key_id=COS_HMAC_ACCESS_KEY_ID,
    aws_secret_access_key=COS_HMAC_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    endpoint_url=COS_ENDPOINT
)

# Fonction pour créer un fichier texte dans un bucket
def create_text_file(bucket_name, item_name, file_text):
    print(f"Creating new item: {item_name} in bucket: {bucket_name}")
    try:
        # Envoi du fichier au bucket COS
        cos_client.put_object(
            Bucket=bucket_name,
            Key=item_name,
            Body=file_text
        )
        print(f"Item: {item_name} created successfully!")
    except ClientError as be:
        print(f"CLIENT ERROR: {be}\n")
    except Exception as e:
        print(f"Unable to create text file: {e}")

# Exemple d'utilisation
bucket_name = "bu0021009393"  # Nom du bucket COS
item_name = "test_file.txt"  # Nom du fichier à créer
file_text = "Ceci est un test d'envoi vers IBM COS avec HMAC."  # Contenu du fichier

# Appel de la fonction pour créer le fichier dans le bucket
create_text_file(bucket_name, item_name, file_text)
