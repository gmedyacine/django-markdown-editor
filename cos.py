import ibm_boto3
from ibm_botocore.client import Config, ClientError

# Configuration avec les informations d'authentification HMAC
COS_ENDPOINT = "https://bu0021009393.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4229"
COS_HMAC_ACCESS_KEY_ID = "8cac968e8be4775a706551937d1bd1a"  # Access key HMAC
COS_HMAC_SECRET_ACCESS_KEY = "9bdadc074ae7ae587e4df4..."  # Secret key HMAC

# Fonction de test de connexion à IBM COS
def test_cos_connection():
    try:
        # Création du client COS avec HMAC
        print("Testing connection to IBM COS...")
        cos_client = ibm_boto3.client(
            "s3",
            aws_access_key_id=COS_HMAC_ACCESS_KEY_ID,
            aws_secret_access_key=COS_HMAC_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            endpoint_url=COS_ENDPOINT
        )
        # Vérification de la liste des buckets pour tester la connexion
        response = cos_client.list_buckets()
        print("Connection successful! Buckets found:")
        for bucket in response["Buckets"]:
            print(f" - {bucket['Name']}")
        return cos_client
    except ClientError as e:
        print(f"Client error: {e}")
        return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

# Fonction pour créer un fichier texte dans un bucket
def create_text_file(cos_client, bucket_name, item_name, file_text):
    if cos_client is None:
        print("Unable to create file: No connection to COS.")
        return

    print(f"Creating new item: {item_name} in bucket: {bucket_name}")
    try:
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

# Exécution du script
if __name__ == "__main__":
    # Test de connexion
    cos_client = test_cos_connection()

    # Tentative de création de fichier si la connexion a réussi
    bucket_name = "bu0021009393"  # Nom du bucket COS
    item_name = "test_file.txt"  # Nom du fichier
    file_text = "Ceci est un test d'envoi vers IBM COS avec HMAC."  # Contenu du fichier

    # Création du fichier dans le bucket
    create_text_file(cos_client, bucket_name, item_name, file_text)
