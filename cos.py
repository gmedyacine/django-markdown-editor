import ibm_boto3
from ibm_botocore.client import Config

# Configuration des informations d'authentification
cos_endpoint = "https://bu0021009393.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4229"
cos_access_key_id = "8cac968e8be4775a706551937d1bd1a"  # Clé d'accès HMAC
cos_secret_access_key = "9bdadc074ae7ae587e4df4..."  # Clé secrète HMAC

# Création du client IBM COS avec HMAC
cos = ibm_boto3.client(
    "s3",
    aws_access_key_id=cos_access_key_id,
    aws_secret_access_key=cos_secret_access_key,
    config=Config(signature_version="s3v4"),
    endpoint_url=cos_endpoint,
)

# Fonction pour lister le contenu du bucket
def list_bucket_contents(bucket_name):
    try:
        response = cos.list_objects_v2(Bucket=bucket_name)
        if "Contents" in response:
            print("Liste des objets dans le bucket:")
            for obj in response["Contents"]:
                print(f" - {obj['Key']} (taille: {obj['Size']} octets)")
        else:
            print("Aucun objet trouvé dans le bucket.")
    except Exception as e:
        print(f"Erreur d'accès à COS: {e}")

# Utilisation de la fonction
bucket_name = "bu0021009393"
list_bucket_contents(bucket_name)
