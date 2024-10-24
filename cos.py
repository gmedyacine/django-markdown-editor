import ibm_boto3
from ibm_botocore.client import Config

# Configuration des informations d'authentification
cos_endpoint = "https://bu0021009393.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4229"
cos_access_key_id = "8cac968e8be4775a706551937d1bd1a"
cos_secret_access_key = "9bdadc074ae7ae587e4df4..."

# Création du client COS
cos = ibm_boto3.client(
    "s3",
    ibm_api_key_id=cos_access_key_id,
    ibm_service_instance_id=cos_secret_access_key,
    config=Config(signature_version="oauth"),
    endpoint_url=cos_endpoint,
)

# Fonction pour lister les objets du bucket
def list_bucket_contents(bucket_name):
    try:
        response = cos.list_objects_v2(Bucket=bucket_name)
        if "Contents" in response:
            for obj in response["Contents"]:
                print(f"Object: {obj['Key']}  Size: {obj['Size']}")
        else:
            print("No objects in the bucket.")
    except Exception as e:
        print(f"Error accessing COS: {e}")

# Utilisation de la fonction
list_bucket_contents("bu0021009393")
