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

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=os.path.basename(backup_path))

        s3 = boto3.client("s3")

        s3_key = os.path.join(bucket_key_prefix, repo_name, archive_name).replace("\\", "/")

        s3.upload_file(archive_path, bucket, s3_key)

        return {
            "message": "backup to s3 ran successfully",
            "status": True
        }
    except Exception as e:
        return {
            "message": f"backup to s3 failed. Error: {e}",
            "status": False
        }

def cleanup_old_s3_backups(repo_name):
    try:
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

        for _, key in backups[max_entries:]:
            s3.delete_object(Bucket=bucket, Key=key)
        
        return {
            "message": "cleanup ran successfully",
            "status": True
        }
    except Exception as e:
        return {
            "message": f"cleanup failed. Error: {e}",
            "status": False
        }