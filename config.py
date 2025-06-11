from pathlib import Path
from pydantic import BaseSettings, PostgresDsn, Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Historical Architecture in Disaster Zones"
    DATA_DIR: Path = Path(__file__).parents[0] / "data"
    LOG_LEVEL: str = "INFO"

    POSTGRES_DSN: PostgresDsn = Field(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/antakya",
        env="POSTGRES_DSN",
    )

    ARCHNET_API_KEY: str = Field(..., env="ARCHNET_API_KEY")
    EUROPEANA_API_KEY: str = Field(..., env="EUROPEANA_API_KEY")
    DPLA_API_KEY: str = Field(..., env="DPLA_API_KEY")

    COLMAP_BIN: Path = Field("colmap", env="COLMAP_BIN")
    OPENMVS_BIN: Path = Field("OpenMVS", env="OPENMVS_BIN")
    PYTORCH_DEVICE: str = "cuda"

    class Config:
        env_file = ".env"


settings = Settings()
