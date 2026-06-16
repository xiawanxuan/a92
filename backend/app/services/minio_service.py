from minio import Minio
from minio.error import S3Error
from io import BytesIO
from typing import Optional, Tuple
import uuid
from ..core.config import settings


class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"MinIO bucket error: {e}")

    def upload_image(self, file_data: bytes, filename: str, content_type: str) -> Tuple[str, str]:
        object_name = f"images/{uuid.uuid4()}/{filename}"
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return self.bucket, object_name
        except S3Error as e:
            raise Exception(f"Failed to upload to MinIO: {e}")

    def get_image(self, object_name: str) -> BytesIO:
        try:
            response = self.client.get_object(self.bucket, object_name)
            return BytesIO(response.read())
        except S3Error as e:
            raise Exception(f"Failed to get image from MinIO: {e}")

    def get_image_url(self, object_name: str, expires: int = 3600) -> str:
        try:
            return self.client.presigned_get_object(self.bucket, object_name, expires=expires)
        except S3Error as e:
            raise Exception(f"Failed to get presigned URL: {e}")

    def delete_image(self, object_name: str) -> bool:
        try:
            self.client.remove_object(self.bucket, object_name)
            return True
        except S3Error as e:
            print(f"Failed to delete image: {e}")
            return False
