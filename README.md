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

### Secrets

RepoVault expects 3 secrets to exists:

- An API key. Used to authenticate with the Lambda. When cached its stored hashed.

- Github PAT. Used to authenticate with Github. Only needed if used on private repository.

- Discord webhook. Used to alert when either API key mismatch or disallowed client IP interacting with the Lambda.

### S3 Bucket

- Stores compressed backups (.tar.gz)

- Automatically retains the latest 10 backups

---

## Deployment

### Environment Variables

When deploying the container image to a Lambda function you will need these environment variables:
 
- `SECRET_NAME`. The secret name that the needed secrets exist.

- `API_SECRET_NAME`. The key for the API key.

- `GITHUB_PAT_SECRET_NAME`. The key for the PAT.

- `DISCORD_WEBHOOK_SECRET_NAME`. The key for the Discord webhook.

- `BUCKET`. The bucket where backups will be uploaded to.

- `BUCKET_KEY`. The bucket key prefix where backups will be uploaded to(Optional).

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