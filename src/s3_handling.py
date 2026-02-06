import boto3
import os
import tempfile
import tarfile

def backup_repos_s3_bucket(timestamp, backup_path, repo_name):
    try:
        bucket = "blue-bucket-general-purpose"
        bucket_key_prefix = "repo_backups_lambda_function"

        archive_name = f"{timestamp}.tar.gz"
        archive_path = os.path.join(tempfile.gettempdir(), archive_name)

        print("[~] Compressing backup...")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=os.path.basename(backup_path))
        print("[+] Compressing finished")

        s3 = boto3.client("s3")

        s3_key = os.path.join(bucket_key_prefix, repo_name, archive_name).replace("\\", "/")

        print("[~] Uploading backup to s3...")
        s3.upload_file(archive_path, bucket, s3_key)
        print("[+] Upload finished")

        return {
            "message": "backup to s3 ran successfully",
            "status": True,
            "extra": None
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

        bucket = "blue-bucket-general-purpose"
        bucket_key_prefix = "repo_backups_lambda_function"

        prefix = f"{bucket_key_prefix}/{repo_name}/"

        s3 = boto3.client("s3")

        paginator = s3.get_paginator("list_objects_v2")

        backups = []

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]

                if key.endswith(".tar.gz"):
                    filename = os.path.basename(key)
                    timestamp = filename.replace(".tar.gz", "")
                    backups.append((timestamp, key))

        backups.sort(key=lambda x: x[0], reverse=True)

        deleted_backups = []

        for timestamp, key in backups[max_entries:]:
            s3.delete_object(Bucket=bucket, Key=key)
            deleted_backups.append(timestamp)

        print("[+] Cleanup of s3 backups finished")

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
    