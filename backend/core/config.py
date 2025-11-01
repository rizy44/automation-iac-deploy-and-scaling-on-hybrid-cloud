import os
from pathlib import Path
from dotenv import load_dotenv

# load .env ở root repo
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

class Settings:
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8008"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENV: str = os.getenv("ENV", "dev")

    TEMPLATE_DIR: Path = Path(os.getenv("TEMPLATE_DIR", "backend/templates")).resolve()
    TF_BIN: str = os.getenv("TF_BIN", "/usr/bin/terraform")
    TF_WORK_ROOT: Path = Path(os.getenv("TF_WORK_ROOT", ".infra/work")).resolve()
    TF_TIMEOUT_SEC: int = int(os.getenv("TF_TIMEOUT_SEC", "900"))

    DEFAULT_REGION: str = os.getenv("DEFAULT_REGION", "ap-southeast-2")
    DEFAULT_AZ: str = os.getenv("DEFAULT_AZ", "ap-southeast-2a")
    DEFAULT_INSTANCE_TYPE: str = os.getenv("DEFAULT_INSTANCE_TYPE", "t3.micro")

    # ==== ONLY TWO AWS CREDS ====
    AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")

settings = Settings()
settings.TF_WORK_ROOT.mkdir(parents=True, exist_ok=True)
