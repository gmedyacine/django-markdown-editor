import requests

# Define Vault details
VAULT_URL = "https://hvault.staging.echonet"
VAULT_NAMESPACE = "UPM_CARDIF/8705/EC002I002860"
CERT_PATH = "/path/to/certificate.pem"
KEY_PATH = "/path/to/private.key"

# Step 1: Authenticate with Vault using the client certificate
auth_url = f"{VAULT_URL}/v1/auth/cert/login"
headers = {
    "X-Vault-Namespace": VAULT_NAMESPACE,
    "X-Vault-Request": "true"
}

# Perform the authentication request
try:
    response = requests.post(auth_url, headers=headers, cert=(CERT_PATH, KEY_PATH), verify=False)
    response.raise_for_status()
    VAULT_TOKEN = response.json()["auth"]["client_token"]
    print(f"Vault authentication successful. Token: {VAULT_TOKEN}")
except requests.exceptions.RequestException as e:
    print(f"Authentication failed: {e}")
    exit(1)

# Step 2: Use the token to access secrets
secret_path = "v1/UPM_CARDIF/8705/EC002I002860/objsto/kv/co002i005676"
secret_url = f"{VAULT_URL}/{secret_path}"
headers["X-Vault-Token"] = VAULT_TOKEN

try:
    response = requests.get(secret_url, headers=headers, verify=False)
    response.raise_for_status()
    secrets = response.json()["data"]["data"]  # Extract secrets
    print(f"Secrets retrieved successfully: {secrets}")
except requests.exceptions.RequestException as e:
    print(f"Failed to retrieve secrets: {e}")
