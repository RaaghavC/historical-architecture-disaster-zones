from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:  # pydantic <2.0
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Historical Architecture in Disaster Zones"
    DATA_DIR: Path = Path(__file__).parents[0] / "data"
    LOG_LEVEL: str = "INFO"

    POSTGRES_DSN: str = Field(
        "sqlite:///:memory:",
        env="POSTGRES_DSN",
    )

    ARCHNET_API_KEY: str = Field("dummy", env="ARCHNET_API_KEY")
    EUROPEANA_API_KEY: str = Field("dummy", env="EUROPEANA_API_KEY")
    DPLA_API_KEY: str = Field("dummy", env="DPLA_API_KEY")

    COLMAP_BIN: Path = Field("colmap", env="COLMAP_BIN")
    OPENMVS_BIN: Path = Field("OpenMVS", env="OPENMVS_BIN")
    PYTORCH_DEVICE: str = "cuda"

    class Config:
        env_file = ".env"


settings = Settings()
