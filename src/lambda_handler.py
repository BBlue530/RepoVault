import os
import subprocess
import datetime
import json
import traceback
import hashlib
import shutil
from urllib.parse import unquote
from s3_handling import backup_repos_s3_bucket, cleanup_old_s3_backups
from secret_manager import read_api_key_secret, read_discord_webhook_secret, read_pat_secret
from helpers import sterilize_output
from ip_whitelist import verify_ip_whitelist
from alert import alert_webhook

def lambda_backup_repository(event, context):
    body = event.get("body")
    if body:
        event_body = json.loads(body)

    received_api_key = unquote(event_body.get("api_key", ""))
    hashed_received_api_key = hashlib.sha256(received_api_key.encode("utf-8")).hexdigest()

    repo_url = unquote(event_body.get("repo_url", ""))

    client_ip = event.get("requestContext", {}).get("http", {}).get("sourceIp")
    print(f"[+] Client ip: [{client_ip}]")
    print(f"[+] Received repository url: [{repo_url}]")

    if not verify_ip_whitelist(client_ip):
        print("[!] Client ip not found in whitelist")
        print(f"[!] Received hashed API key: [{hashed_received_api_key}]")

        DISCORD_WEBHOOK = read_discord_webhook_secret()
        alert_webhook(DISCORD_WEBHOOK, "Client IP not found in whitelist", "A client IP attempted to interact with lambda function.", context)

        return {
            "statusCode": 403,
            "body": json.dumps({"error": "IP not allowed"})
            }
    
    HASHED_API_KEY = read_api_key_secret()

    print(f"[+] Hashed received API key: [{hashed_received_api_key}]")
    print(f"[+] Hashed API key: [{HASHED_API_KEY}]")

    if hashed_received_api_key != HASHED_API_KEY:
        print("[!] API key mismatch")
        print(f"[!] Received hashed API key: [{hashed_received_api_key}]")

        DISCORD_WEBHOOK = read_discord_webhook_secret()
        alert_webhook(DISCORD_WEBHOOK, "API key mismatch", "API key mismatch.", context)

        return {
            "statusCode": 400,
            "body": json.dumps({"error": "api key mismatch"})
            }
        
    try:
        PAT = read_pat_secret()
        
        repo_git = repo_url.split("/")[-1]
        repo_name = repo_git.replace(".git", "")
        auth_repo_url = repo_url.replace("https://", f"https://{PAT}@")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = os.path.join("/tmp", repo_name, timestamp)

        git_backup_path = os.path.join(backup_path, f"{repo_name}.git")
        git_working_backup_path = os.path.join(backup_path, repo_name)
        bundle_path = os.path.join(backup_path, f"{repo_name}_full_backup.bundle")

        os.makedirs(backup_path, exist_ok=True)

        sterilized_mirror_clone_result = ""
        sterilized_clone_result = ""
        sterilized_bundle_result = ""

        try:
            print("[~] Mirror repo...")
            mirror_clone_result = subprocess.run(f'git clone --mirror "{auth_repo_url}" "{git_backup_path}"', shell=True, capture_output=True, text=True, check=True)
            sterilized_mirror_clone_result = sterilize_output(mirror_clone_result, PAT)
            print("[+] Mirror repo finished")

            print("[~] Clone repo...")
            clone_result = subprocess.run(f'git clone "{auth_repo_url}" "{git_working_backup_path}"', shell=True, capture_output=True, text=True, check=True)
            sterilized_clone_result = sterilize_output(clone_result, PAT)
            print("[+] Clone repo finished")

            print("[~] Bundle repo...")
            bundle_result = subprocess.run(f'git --git-dir="{git_backup_path}" bundle create "{bundle_path}" --all', shell=True, capture_output=True, text=True, check=True)
            sterilized_bundle_result = sterilize_output(bundle_result, PAT)
            print("[+] Bundle repo finished")

            git_result = {
                "message": "git ran successfully",
                "status": True,
                "extra": {
                    "mirror_clone_result": sterilized_mirror_clone_result,
                    "clone_result": sterilized_clone_result,
                    "bundle_result": sterilized_bundle_result
                }
            }

        except subprocess.CalledProcessError as e:
            sterilized_error = sterilize_output(e, PAT)

            print(f"[!] Git failed. Error: [{sterilized_error}]")

            git_result = {
                "message": "git failed",
                "status": False,
                "extra": {
                    "error": sterilized_error,
                    "mirror_clone_result": sterilized_mirror_clone_result,
                    "clone_result": sterilized_clone_result,
                    "bundle_result": sterilized_bundle_result
                }
            }
            return {
                    "statusCode": 500,
                    "body": json.dumps({
                    "git_result": git_result,
                })
            }

        backup_repos_result = backup_repos_s3_bucket(timestamp, backup_path, repo_name)
        
        if not backup_repos_result.get("status"):
            return {
                    "statusCode": 500,
                    "body": json.dumps({
                    "backup_repos_result": backup_repos_result,
                    "git_result": git_result,
                })
            }

        cleanup_old_s3_result = cleanup_old_s3_backups(repo_name)

        if not backup_repos_result.get("status") or not cleanup_old_s3_result.get("status") or not git_result.get("status"):
            print("[!] Backup failed")
            statusCode = 500
        else:
            print("[+] Backup finished")
            statusCode = 200

        return {
                "statusCode": statusCode,
                "body": json.dumps({
                    "backup_repos_result": backup_repos_result,
                    "cleanup_old_s3_result": cleanup_old_s3_result,
                    "git_result": git_result,
                })
            }

    except Exception as e:
        tb = traceback.format_exc()
        lambda_status = {
            "message": "lambda failed",
            "status": False,
            "extra": {
                "error": str(e),
                "traceback": tb
            }
        }
        return {
            "statusCode": 500,
            "body": lambda_status
            }
    
    finally:
        shutil.rmtree(os.path.join("/tmp", repo_name), ignore_errors=True)