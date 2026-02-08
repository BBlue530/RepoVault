# RepoVault

RepoVault is a fully automated AWS Lambda solution for backing up Git repositories to S3 using Containerized Lambda functions. RepoVault provides repository mirroring, cloning, bundling, and backup cleanup with secure API key authentication.

---

## Features

- Clone and mirror Git repositories (full history included)

- Create Git bundle backups for full repository state

- Compress backups and upload to S3

- Automatic cleanup of old S3 backups, keeping the latest 10

- Secure access using API key authentication

- Containerized Lambda function for consistent deployment

- IP whitelist to only allow GitHub Actions access

- Alerts using Discord webhook

---

## Architecture

### Lambda Function

```
AWS Lambda Function
        │
        └─Receive repository URL + API key
            │
            └─Verify client IP against GitHub Actions whitelist
                │   └─Reject if not allowed (403)
                │
                └─Validate API key
                    │   └─Load hashed key from cache
                    │       └─Fetch from AWS Secrets Manager if not cached yet
                    │           └─Cache secret
                    │
                    ├─Clone repository
                    │   ├─Mirror clone
                    │   ├─Standard clone
                    │   └─Create bundle backup
                    │
                    ├─Compress backup artifacts
                    │   └─Upload backups to Amazon S3
                    │
                    └─Cleanup old S3 backups (retain latest 10)
```

### AWS Secrets Manager

The Lambda expects 3 secrets to exists in secret name `repo_backup_secrets`:

- `api_key`. Used to authenticate with the Lambda. When cached its stored hashed.

- `github_pat`. Used to authenticate with Github. Only needed if used on private repository.

- `discord_webhook`. Used to alert when either API key mismatch or disallowed client IP interacting with the Lambda.

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