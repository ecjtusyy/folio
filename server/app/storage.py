from __future__ import annotations
import boto3
from botocore.config import Config
from .config import settings

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
        verify=False,
    )

def ensure_bucket():
    s3=get_s3_client()
    try:
        s3.head_bucket(Bucket=settings.minio_bucket)
    except Exception:
        s3.create_bucket(Bucket=settings.minio_bucket)

def put_bytes(data: bytes, key: str, content_type: str):
    s3=get_s3_client()
    s3.put_object(Bucket=settings.minio_bucket, Key=key, Body=data, ContentType=content_type)

def head_object(key: str):
    s3=get_s3_client()
    return s3.head_object(Bucket=settings.minio_bucket, Key=key)

def stream_object(key: str):
    s3=get_s3_client()
    obj=s3.get_object(Bucket=settings.minio_bucket, Key=key)
    body=obj["Body"]
    def it(chunk=262144):
        while True:
            b=body.read(chunk)
            if not b:
                break
            yield b
    return it(), {"content_length": obj.get("ContentLength")}
