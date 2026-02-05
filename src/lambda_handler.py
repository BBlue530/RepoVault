import boto3
import os
import subprocess
import datetime
import base64
import json
from urllib.parse import unquote
from s3_handling import backup_repos_s3_bucket, cleanup_old_s3_backups
from variables import *

def lambda_backup_repository(event, context):
    body = event.get("body")
    if body:
        event = json.loads(body)

    received_api_key = unquote(event.get("api_key", ""))
    repo_url = unquote(event.get("repo_url", ""))

    API_KEY = read_secret_from_secret_manager(api_key_secret_name, secret_name)

    if received_api_key != API_KEY:
        return {
            "statusCode": 400,
            "body": "api key mismatch"
            }
    
    pat = read_secret_from_secret_manager(github_pat_secret_name, secret_name)
    
    repo_git = repo_url.split("/")[-1]
    repo_name = repo_git.replace(".git", "")
    auth_repo_url = repo_url.replace("https://", f"https://{pat}@")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = os.path.join(repo_name, timestamp)

    git_backup_path = os.path.join(backup_path, f"{repo_name}.git")
    git_working_backup_path = os.path.join(backup_path, repo_name)
    bundle_path = os.path.join(backup_path, f"{repo_name}_full_backup.bundle")

    os.makedirs(backup_path, exist_ok=True)

    subprocess.run(f'git clone --mirror "{auth_repo_url}" "{git_backup_path}"', shell=True, capture_output=True, text=True)

    subprocess.run(f'git clone "{auth_repo_url}" "{git_working_backup_path}"', shell=True, capture_output=True, text=True)
    
    subprocess.run(f'git --git-dir="{git_backup_path}" bundle create "{bundle_path}" --all', shell=True, capture_output=True, text=True)

    backup_repos_s3_bucket(timestamp, backup_path, repo_name)
    cleanup_old_s3_backups(timestamp, repo_name)

    return {
            "statusCode": 200,
            "body": "backup succeeded"
            }

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