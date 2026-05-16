import os
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

# Ett lokalt testscript för autentisering. Det behövs inte i produktion, 
# men är bra i dev för att verifiera att .env och Service Principal fungerar innan vi felsöker Airflow/DAG/Fabric.


# Load environment variables from .env file
load_dotenv()

try:
    # Get credentials from environment variables
    client_id = os.getenv('AZURE_CLIENT_ID')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')

    # Validate that all required environment variables are present
    if not all([client_id, tenant_id, client_secret]):
        missing_vars = []
        if not client_id:
            missing_vars.append('AZURE_CLIENT_ID')
        if not tenant_id:
            missing_vars.append('AZURE_TENANT_ID')
        if not client_secret:
            missing_vars.append('AZURE_CLIENT_SECRET')
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Create the credential object
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    # Define the scope - adjust this based on your needs
    # Common scopes:
    # - "https://graph.microsoft.com/.default" for Microsoft Graph
    # - "https://management.azure.com/.default" for Azure Resource Manager
    # - "https://storage.azure.com/.default" for Azure Storage
    scope = "https://api.fabric.microsoft.com/.default"

    # Get the access token
    token = credential.get_token(scope)

    print("Token retrieved successfully!")
    print(f"Token expires at: {token.expires_on}")
    print(f"Token: {token.token}")

except Exception as e:
    print(f"Error retrieving token: {str(e)}")
