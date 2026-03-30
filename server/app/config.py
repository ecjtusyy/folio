from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")
    admin_username: str = "admin"
    admin_password: str = "admin123"
    jwt_secret: str = "dev_jwt_secret_change_me"
    session_expire_hours: int = 24
    file_token_ttl_seconds: int = 300
    app_data_dir: str = "/mnt/d/app-data"
    app_tmp_dir: str = "/mnt/d/app-data/tmp"
    app_log_dir: str = "/mnt/d/app-data/logs"
    database_url: str = "postgresql+psycopg://app:app_pw@postgres:5432/appdb"
    minio_endpoint: str = "http://minio:9000"
    minio_access_key: str = "minio"
    minio_secret_key: str = "minio12345"
    minio_bucket: str = "app"
    onlyoffice_internal_url: str = "http://onlyoffice"
    internal_server_base_url: str = "http://server:8000"
    tex_compile_timeout_seconds: int = 90
    tex_log_tail_lines: int = 80

settings = Settings()
