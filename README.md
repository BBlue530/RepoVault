# Backup Repo Lambda

A fully automated AWS Lambda solution for backing up Git repositories to S3 using Containerized Lambda functions. This project provides repository mirroring, cloning, bundling, and backup cleanup with secure API key authentication.

---

## Features

- Clone and mirror Git repositories (full history included)

- Create Git bundle backups for full repository state

- Compress backups and upload to S3

- Automatic cleanup of old S3 backups, keeping the latest 10

- Secure access using API key authentication

- Containerized Lambda function for consistent deployment

---

## Architecture

### Lambda Function

- Receives Git repository URL and API key

- Validates API key against AWS Secrets Manager

- Clones repository (mirror and normal)

- Creates a bundle backup of the repo

- Uploads backups to S3

- Cleans up old backups in S3

### AWS Secrets Manager

- Stores GitHub Personal Access Token (PAT)

- Stores API key for Lambda authentication

### S3 Bucket

- Stores compressed backups (.tar.gz)

- Automatically retains the latest 10 backups

---

## Usage

Invoke the Lambda via API request:

```
curl -X POST "$LAMBDA_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
        "api_key": "YOUR_API_KEY",
        "repo_url": "https://github.com/username/repo.git"
      }'
```

---