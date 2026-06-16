from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Sonar Classification System"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql://postgres:postgres@localhost:5432/sonar_db"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "sonar-images"

    redis_url: str = "redis://localhost:6379/0"

    model_path: str = "./backend/models/resnet50_sonar.pth"
    device: str = "cpu"
    batch_size: int = 16
    tile_size: int = 512

    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
