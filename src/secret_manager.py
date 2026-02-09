import boto3
import base64
import json
import hashlib
import os

HASHED_API_KEY = None
DISCORD_WEBHOOK = None
PAT = None

def read_secret_from_secret_manager(secret_key_name, secret_name):
    client = boto3.client("secretsmanager")

    response = client.get_secret_value(SecretId=secret_name)

    if "SecretString" in response:
        secret_payload = response["SecretString"]
    else:
        secret_payload = base64.b64decode(response["SecretBinary"]).decode("utf-8")

    try:
        secret_obj = json.loads(secret_payload)
    except json.JSONDecodeError:
        raise ValueError("Secret is not valid JSON")

    if secret_key_name not in secret_obj:
        raise KeyError(f"[!] Key: '{secret_key_name}' not found in secret '{secret_name}'")

    return secret_obj[secret_key_name]

def read_api_key_secret():
    global HASHED_API_KEY
    secret_name = os.environ.get("SECRET_NAME")
    api_key_secret_name = os.environ.get("API_SECRET_NAME")
    
    if HASHED_API_KEY is not None:
        print("[+] API key already present")
        return HASHED_API_KEY
    
    print("[+] Calling secret manager for API key")
    API_KEY = read_secret_from_secret_manager(api_key_secret_name, secret_name)
    HASHED_API_KEY = hashlib.sha256(API_KEY.encode("utf-8")).hexdigest()
    return HASHED_API_KEY

def read_discord_webhook_secret():
    global DISCORD_WEBHOOK
    secret_name = os.environ.get("SECRET_NAME")
    discord_webhook_secret_name = os.environ.get("DISCORD_WEBHOOK_SECRET_NAME")

    if DISCORD_WEBHOOK is not None:
        print("[+] Discord webhook already present")
        return DISCORD_WEBHOOK
    
    print("[+] Calling secret manager for Discord webhook")
    DISCORD_WEBHOOK = read_secret_from_secret_manager(discord_webhook_secret_name, secret_name)
    return DISCORD_WEBHOOK

def read_pat_secret():
    global PAT
    secret_name = os.environ.get("SECRET_NAME")
    github_pat_secret_name = os.environ.get("GITHUB_PAT_SECRET_NAME")

    if PAT is not None:
        print("[+] PAT already present")
        return PAT
    
    print("[+] Calling secret manager for PAT")
    PAT = read_secret_from_secret_manager(github_pat_secret_name, secret_name)
    return PAT