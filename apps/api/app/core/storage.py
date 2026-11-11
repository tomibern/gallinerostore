"""Cliente S3 (RustFS/MinIO en local; R2 o Supabase Storage en producción)."""

import json

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


def allow_public_read(s3: S3Client, bucket: str) -> None:
    """Lectura anónima de los archivos del bucket: las fotos del catálogo son públicas."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))


def get_s3(request: Request) -> S3Client:
    client: S3Client = request.app.state.s3
    return client


class ObjectStorage:
    """Archivos en un bucket S3. En la base se guardan claves (rutas), nunca URLs."""

    def __init__(self, s3: S3Client, bucket: str) -> None:
        self._s3 = s3
        self.bucket = bucket

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self.bucket, Key=key)
        except self._s3.exceptions.ClientError:
            return False
        return True

    def list_keys(self, prefix: str) -> list[str]:
        paginator = self._s3.get_paginator("list_objects_v2")
        return sorted(
            obj["Key"]
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
        )

    def delete_prefix(self, prefix: str) -> int:
        """Borra todos los archivos bajo el prefijo. Devuelve cuántos borró."""
        keys = self.list_keys(prefix)
        for start in range(0, len(keys), 1000):  # máximo por pedido en S3
            batch = keys[start : start + 1000]
            self._s3.delete_objects(
                Bucket=self.bucket, Delete={"Objects": [{"Key": k} for k in batch]}
            )
        return len(keys)
