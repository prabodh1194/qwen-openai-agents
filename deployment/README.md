# BSE News Analyzer - AWS Lambda Deployment

This directory contains deployment scripts and infrastructure code for deploying the BSE News Analyzer to AWS Lambda with S3 mountpoint support.

## Architecture

- **AWS Lambda**: Python function with S3 mountpoint
- **S3 Mountpoint**: Maps S3 bucket to Lambda's `$HOME` directory
- **Credentials**: Stored at `~/.qwen/oauth_creds.json` (mounted from S3)
- **Stocks List**: Stored at `~/stocks/stocks_100` (mounted from S3)
- **Outputs**: Saved to `outputs/` directory (mounted to S3)

## Deployment Steps

### 1. Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform installed
- uv package manager installed
- Qwen credentials at `~/.qwen/oauth_creds.json`

### 2. Build Lambda Package

```bash
uv run deployment/scripts/build.py
```

### 3. Upload Credentials and Stocks to S3

```bash
uv run deployment/scripts/upload_creds.py --bucket your-bucket-name --region us-east-1
```

### 4. Deploy Infrastructure

```bash
uv run deployment/scripts/deploy.py
```

### 5. Test the Function

After deployment, you can invoke the Lambda function:

```bash
# Using AWS CLI
aws lambda invoke --function-name bse-news-analyzer --payload '{"company_name":"Infosys"}' response.json

# Or via HTTP (if Function URL is enabled)
curl -X POST https://your-function-url.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Infosys"}'
```

## Scripts

### build.py
Builds the Lambda deployment package with all dependencies.

### upload_creds.py
Uploads Qwen credentials and stocks file to S3 for mountpoint access.

### deploy.py
Deploys Terraform infrastructure.

## Terraform Configuration

The Terraform configuration creates:

- S3 bucket for mountpoint
- IAM role with S3 permissions
- Lambda function with S3 mountpoint
- Lambda Function URL (optional)

## Environment Variables

- `HOME`: Set to `/home/sbx_user1050` for S3 mountpoint compatibility

## Notes

- The S3 mountpoint maps the entire bucket to the Lambda's home directory
- Credentials should be uploaded to `s3://bucket-name/.qwen/oauth_creds.json`
- Analysis outputs are saved to `s3://bucket-name/outputs/`
- Ensure the IAM role has appropriate S3 permissions