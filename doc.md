## Introduction
This document explains how to use credentials and configuration details stored in HashiCorp Vault and DMZR to establish a secure connection to a Redis database from a workspace in Domino. The instructions cover two methods for connecting: using Python and cURL, with a focus on securely retrieving the necessary secrets from Vault.

## Prerequisites
Before proceeding, ensure that you have access to the following:

1- Redis endpoint: Provided by DMZR (e.g., rd0021000358.svc-np.paas.echonet:30510).
2- Namespace: The namespace for Vault (e.g., UPM_CARDIF/8785/EC002102860).
3- HashiCorp Vault URL: The Vault API endpoint (e.g., https://hvault.staging.echonet.com).
4- Vault token: An authentication token for accessing Vault.
5- SSL certificate: Retrieved from Vault for secure connections.
Make sure that the hvault environment is properly configured to allow access to the Redis secrets.

## Step-by-Step Guide
1. Retrieve Redis Credentials from HashiCorp Vault
You need to use the Vault API to retrieve the credentials for connecting to Redis. These credentials are stored under a specific namespace and secret path in Vault.

### Python Example:
Here’s how to retrieve the Redis credentials using the Vault API in Python.
```
import requests
import base64
import redis

# Vault parameters
vault_url = "https://hvault.staging.echonet.com"
vault_token = "your_vault_token_here"
vault_namespace = "UPM_CARDIF/8785/EC002102860"
secret_path = "cloud/data/redis/RDO021000358"

# Function to get secrets from Vault
def get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace):
    url = f"{vault_url}/v1/{secret_path}"
    headers = {
        "X-Vault-Token": vault_token,
        "Accept": "application/json",
        "X-Vault-Namespace": vault_namespace
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['data']
    else:
        raise Exception(f"Error retrieving secret: {response.status_code} {response.text}")

# Fetch the Redis credentials
secret_data = get_secret_from_vault(secret_path, vault_token, vault_url, vault_namespace)

redis_user = secret_data['user']
redis_password = secret_data['password']
redis_cert_base64 = secret_data['certificate']

# Decode the certificate and save it to a file
with open("/tmp/redis_certificate.pem", "w") as cert_file:
    cert_file.write(f"-----BEGIN CERTIFICATE-----\n{redis_cert_base64}\n-----END CERTIFICATE-----")

# Connect to Redis
r = redis.Redis(
    host="rd0021000358.svc-np.paas.echonet",
    port=30510,
    username=redis_user,
    password=redis_password,
    ssl=True,
    ssl_ca_certs="/tmp/redis_certificate.pem",
    decode_responses=True
)

# Test the connection
try:
    r.ping()
    print("Successfully connected to Redis")
except Exception as e:
    print(f"Connection error: {e}")

```
### cURL Example:
You can also use curl to fetch the Redis secrets directly from Vault and interact with Redis.
```
# Fetch secrets from Vault
curl -X GET \
  "https://hvault.staging.echonet.com/v1/cloud/data/redis/RDO021000358" \
  -H "X-Vault-Token: your_vault_token_here" \
  -H "X-Vault-Namespace: UPM_CARDIF/8785/EC002102860" \
  -H "accept: application/json"

# Output example:
# {
#   "data": {
#     "data": {
#       "certificate": "LS0tLS1CRUdJTiBDRV...",
#       "user": "RLE_AP8835_rd0021000358",
#       "password": "ntAA63--rK1Lgz2VRG31X"
#     }
#   }
# }

# Once you have the Redis credentials and the SSL certificate, you can use tools like `stunnel` or direct Redis clients to establish the connection.

```

2. Redis Connection Overview
The connection to Redis is secured with SSL and authenticated using the credentials stored in Vault. Both the user and password are retrieved from Vault, along with the SSL certificate required to validate the connection.

Here’s how the connection flow works:

Retrieve credentials from Vault.
Save the Redis SSL certificate locally.
Use the credentials and certificate to authenticate the Redis connection.
3. Connection Architecture
The following diagram illustrates the architecture of connecting to Redis through HashiCorp Vault from a Domino workspace:

Diagram Description:
Domino Workspace: This is where the connection to Redis is initiated, typically running a Python or curl script.
HashiCorp Vault: Secrets (user, password, certificate) are stored here and are retrieved via the Vault API using an authentication token.
Redis: The target database, which requires SSL for secure communication.
I will generate a diagram to visually represent this.

Troubleshooting
If you encounter any errors during the connection process, consider checking the following:

Ensure that your Vault token is valid and has permission to access the required namespace.
Verify that the Redis endpoint and port are correctly specified.
Make sure the SSL certificate is correctly formatted and placed in a file accessible by your script.
Conclusion
By following these steps, you can securely retrieve Redis credentials from HashiCorp Vault and connect to Redis from a Domino workspace. Both Python and curl methods are available for different use cases. The architecture ensures secure access to secrets and encrypted communication with Redis.

