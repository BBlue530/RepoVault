import boto3
import os
import tempfile
import tarfile
from datetime import datetime
from helpers import format_file_size

def backup_repos_s3_bucket(timestamp, backup_path, repo_name):
    try:
        bucket = os.environ.get("BUCKET")
        bucket_key_prefix = os.environ.get("BUCKET_KEY")

        archive_name = f"{timestamp}.tar.gz"
        archive_path = os.path.join(tempfile.gettempdir(), archive_name)

        print("[~] Compressing backup...")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=os.path.basename(backup_path))
        print("[+] Compressing finished")

        size_bytes = os.path.getsize(archive_path)
        archive_size = format_file_size(size_bytes)
        print(f"[+] Archive size: {archive_size}")

        s3 = boto3.client("s3")

        s3_key = os.path.join(bucket_key_prefix, repo_name, archive_name).replace("\\", "/")

        print(f"[~] Uploading backup to s3://{bucket}/{s3_key}...")
        s3.upload_file(archive_path, bucket, s3_key)
        print("[+] Upload finished")

        return {
            "message": "backup to s3 ran successfully",
            "status": True,
            "extra": {
                "archive_size": archive_size
            }
        }
    
    except Exception as e:
        print(f"[!] Backup to s3 failed. Error: [{str(e)}]")
        return {
            "message": f"backup to s3 failed",
            "status": False,
            "extra": {
                "error": str(e)
            }
        }

def cleanup_old_s3_backups(repo_name):
    try:
        print("[~] Starting cleanup of s3 backups...")
        max_entries=10

        bucket = os.environ.get("BUCKET")
        bucket_key_prefix = os.environ.get("BUCKET_KEY")

        prefix = f"{bucket_key_prefix}/{repo_name}/"

        s3 = boto3.client("s3")

        paginator = s3.get_paginator("list_objects_v2")

        backups = []

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]

                if key.endswith(".tar.gz"):
                    filename = os.path.basename(key)
                    timestamp_str = filename.replace(".tar.gz", "")
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        print(f"[!] Skipping file with invalid timestamp: {filename}")
                        continue
                    backups.append((timestamp_str, timestamp, key))

        backups.sort(key=lambda x: x[0], reverse=True)

        kept_backups = []
        backups_to_delete = []
        deleted_backups = []
        seen_days = set()

        for timestamp_str, timestamp, key in backups:
            day_str = timestamp.strftime("%Y-%m-%d")
            if day_str not in seen_days:
                kept_backups.append((timestamp, key))
                seen_days.add(day_str)
            else:
                backups_to_delete.append((timestamp, key))
                # need to be here or it will crash the lambda. The process still happens but it returns internal error
                deleted_backups.append(timestamp_str)
                print(f"[~] Deleting [{timestamp_str}]...")


        if len(kept_backups) > max_entries:
            to_delete = kept_backups[max_entries:]
            kept_backups = kept_backups[:max_entries]
            backups_to_delete.extend(to_delete)

        for timestamp, key in backups_to_delete:
            s3.delete_object(Bucket=bucket, Key=key)

        print("[+] Cleanup of S3 backups finished")
        print(f"[+] Deleted backups: [{deleted_backups}]")
        print(f"[+] Deleted backups count: [{len(deleted_backups)}]")

        return {
            "message": "cleanup ran successfully",
            "status": True,
            "extra": {
                "deleted_count": len(deleted_backups),
                "deleted_timestamps": deleted_backups
            }
        }
    
    except Exception as e:
        print(f"[!] Cleanup of s3 backups failed. Error: [{str(e)}]")
        return {
            "message": "cleanup failed",
            "status": False,
            "extra": {
                "error": str(e)
            }
        }