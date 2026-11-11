"""Cliente S3 (RustFS/MinIO en local; R2 o Supabase Storage en producción)."""

import boto3
from botocore.config import Config
from fastapi import Request
from mypy_boto3_s3 import S3Client

from app.core.config import Settings


def create_s3_client(settings: Settings) -> S3Client:
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(
            s3={"addressing_style": "path"},
            connect_timeout=3,
            read_timeout=5,
            retries={"max_attempts": 1},
        ),
    )


def ensure_bucket(s3: S3Client, bucket: str) -> bool:
    """Crea el bucket si no existe. Devuelve True si lo creó."""
    existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
    if bucket in existing:
        return False
    s3.create_bucket(Bucket=bucket)
    return True


def get_s3(request: Request) -> S3Client:
    client: S3Client = request.app.state.s3
    return client
