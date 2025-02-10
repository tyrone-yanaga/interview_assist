# this may not be needed, if files are kept on the client device
# altho if u want data persistance, let's say device failure...hmm
# app/services/storage_service.py
import boto3
from core.config import settings

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY
)


def upload_file(file_path: str, bucket: str, object_name: str):
    try:
        s3_client.upload_file(file_path, bucket, object_name)
        return f"s3://{bucket}/{object_name}"
    except Exception as e:
        raise Exception(f"Failed to upload file to S3: {str(e)}")


def download_file(bucket: str, object_name: str, file_path: str):
    try:
        s3_client.download_file(bucket, object_name, file_path)
    except Exception as e:
        raise Exception(f"Failed to download file from S3: {str(e)}")
