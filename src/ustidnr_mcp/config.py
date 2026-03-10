"""Configuration via pydantic-settings."""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    mcp_transport: Literal["stdio", "streamable-http"] = "stdio"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000
    bzst_base_url: str = "https://api.evatr.vies.bzst.de/app/v1/abfrage"
    request_timeout: float = 30.0
    batch_max_size: int = 100
    batch_concurrency: int = 10
    max_input_length: int = 256
    max_vat_id_length: int = 50


settings = Settings()
