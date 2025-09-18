#!/usr/bin/env python3
"""
Create S3 bucket and DynamoDB table for Terraform backend manually.
This is needed before migrating from local state to S3 backend.
"""
import boto3
from botocore.exceptions import ClientError


def create_tfstate_bucket() -> bool:
    """Create S3 bucket for Terraform state with versioning and encryption."""

    s3 = boto3.client("s3", region_name="us-east-1")
    bucket_name = "qwen-openai-agents-tfstate"

    try:
        # Create bucket - us-east-1 doesn't need LocationConstraint
        s3.create_bucket(Bucket=bucket_name)
        print(f"Created S3 bucket: {bucket_name}")

        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"}
        )
        print("Enabled versioning on bucket")

        # Enable encryption
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                ]
            },
        )
        print("Enabled encryption on bucket")

        return True

    except ClientError as e:
        if e.response["Error"]["Code"] == "BucketAlreadyExists":
            print(f"Bucket {bucket_name} already exists")
            return True
        else:
            print(f"Error creating bucket: {e}")
            return False


def create_tfstate_lock_table() -> bool:
    """Create DynamoDB table for Terraform state locking."""

    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    table_name = "qwen-openai-agents-tfstate-lock"

    try:
        # Create table
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "LockID", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "LockID", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created DynamoDB table: {table_name}")

        # Wait for table to be active
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName=table_name)
        print("Table is now active")

        return True

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table {table_name} already exists")
            return True
        else:
            print(f"Error creating table: {e}")
            return False


def main() -> bool:
    """Create both S3 bucket and DynamoDB table."""

    print("Creating Terraform backend resources...")

    bucket_created = create_tfstate_bucket()
    table_created = create_tfstate_lock_table()

    if bucket_created and table_created:
        print("Terraform backend resources created successfully!")
        print("You can now run: make deploy")
        return True
    else:
        print("Failed to create Terraform backend resources")
        return False


if __name__ == "__main__":
    main()
