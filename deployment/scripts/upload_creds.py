"""
Upload credentials to S3 for Lambda mountpoint.
"""
import boto3
import json
from pathlib import Path


def upload_credentials_to_s3(bucket_name: str, region: str = "us-east-1"):
    """Upload credentials to S3 bucket for Lambda mountpoint."""

    # Load local credentials
    creds_path = Path.home() / ".qwen" / "oauth_creds.json"
    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")

    with open(creds_path, "r") as f:
        credentials = json.load(f)

    # Initialize S3 client
    s3 = boto3.client("s3", region_name=region)

    # Upload credentials
    s3_key = ".qwen/oauth_creds.json"
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(credentials, indent=2),
        ContentType="application/json",
    )

    print(f"Credentials uploaded to s3://{bucket_name}/{s3_key}")

    # Create outputs directory structure
    s3.put_object(Bucket=bucket_name, Key="outputs/", Body="")

    print(f"Outputs directory created at s3://{bucket_name}/outputs/")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload credentials to S3")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")

    args = parser.parse_args()
    upload_credentials_to_s3(args.bucket, args.region)
