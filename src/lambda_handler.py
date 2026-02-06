import os
import subprocess
import datetime
import json
import traceback
import hashlib
import hmac
from urllib.parse import unquote
from s3_handling import backup_repos_s3_bucket, cleanup_old_s3_backups
from secret_manager import read_secret_from_secret_manager
from variables import *

def lambda_backup_repository(event, context):
    try:
        body = event.get("body")
        if body:
            event = json.loads(body)

        received_api_key = unquote(event.get("api_key", ""))
        repo_url = unquote(event.get("repo_url", ""))

        API_KEY = read_secret_from_secret_manager(api_key_secret_name, secret_name)

        hashed_received_api_key = hashlib.sha256(received_api_key.encode("utf-8")).hexdigest()
        HASHED_API_KEY = hashlib.sha256(API_KEY.encode("utf-8")).hexdigest()

        print(f"[+] Hashed received API key: [{hashed_received_api_key}]")
        print(f"[+] Hashed API key: [{HASHED_API_KEY}]")

        if received_api_key != API_KEY:
            print("[!] API key mismatch")
            return {
                "statusCode": 400,
                "body": "api key mismatch"
                }
        
        pat = read_secret_from_secret_manager(github_pat_secret_name, secret_name)
        
        repo_git = repo_url.split("/")[-1]
        repo_name = repo_git.replace(".git", "")
        auth_repo_url = repo_url.replace("https://", f"https://{pat}@")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = os.path.join("/tmp", repo_name, timestamp)

        git_backup_path = os.path.join(backup_path, f"{repo_name}.git")
        git_working_backup_path = os.path.join(backup_path, repo_name)
        bundle_path = os.path.join(backup_path, f"{repo_name}_full_backup.bundle")

        os.makedirs(backup_path, exist_ok=True)

        try:
            print("[~] Mirror repo...")
            subprocess.run(f'git clone --mirror "{auth_repo_url}" "{git_backup_path}"', shell=True, capture_output=True, text=True)
            print("[+] Mirror repo finished")

            print("[~] Clone repo...")
            subprocess.run(f'git clone "{auth_repo_url}" "{git_working_backup_path}"', shell=True, capture_output=True, text=True)
            print("[+] Clone repo finished")

            print("[~] Bundle repo...")
            subprocess.run(f'git --git-dir="{git_backup_path}" bundle create "{bundle_path}" --all', shell=True, capture_output=True, text=True)
            print("[+] Bundle repo finished")

            git_result = {
                "message": "git ran successfully",
                "status": True,
                "extra": None
            }

        except subprocess.CalledProcessError as e:
            print(f"[!] Git failed. Error: [{e}]")
            git_result = {
                "message": "git failed",
                "status": False,
                "extra": {
                    "error": e
                }
            }

        backup_repos_result = backup_repos_s3_bucket(timestamp, backup_path, repo_name)
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
                "error": e,
                "traceback": tb
            }
        }
        return {
            "statusCode": 500,
            "body": lambda_status
            }