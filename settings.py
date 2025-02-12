import enum
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()


class Model(str, enum.Enum):
    """Possible models."""

    claude_small = "claude-3-opus-20240229"
    claude_large = "claude-3-5-sonnet-latest"
    openai_small = "gpt-4o"
    openai_large = "o1"


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


# flake8: noqa: E501
def get_opik_url_override(environment: str) -> None:
    """
    Set the OPIK URL override environment variable based on the environment.

    :param environment: The environment to set the override for.
    """
    if environment == "local":
        os.environ["OPIK_URL_OVERRIDE"] = os.getenv("OPIK_URL_OVERRIDE_LOCAL", "")
    if environment == "dev":
        os.environ["OPIK_URL_OVERRIDE"] = os.getenv("OPIK_URL_OVERRIDE_DEV", "")


class Settings(BaseSettings):
    """Application settings configuration."""

    log_level: LogLevel = LogLevel.INFO
    environment: str = "local"
    model: Model = Model.claude_large
    max_tokens: int = 8000
    min_days_for_analysis: int = 60
    default_days: int = 120
    max_retries: int = 3
    retry_delay: int = 2
    finmind_api_key: str = os.getenv("FINMIND_API_KEY")

    # MongoDB settings
    mongo_username: Optional[str] = None
    mongo_password: Optional[str] = None
    mongo_database: Optional[str] = None
    mongo_collection: Optional[str] = None
    
    # MySQL settings
    mysql_database: Optional[str] = None
    mysql_root_password: Optional[str] = None
    
    # RabbitMQ settings
    rabbitmq_default_user: Optional[str] = None
    rabbitmq_default_pass: Optional[str] = None
    
    # Redis settings
    redis_password: Optional[str] = None
    
    # API keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    alphavantage_api_key: Optional[str] = None
    yahoo_finance_api_key: Optional[str] = None
    
    # OPIK settings
    opik_url_override_local: Optional[str] = None
    opik_url_override_dev: Optional[str] = None
    opik_use_local: Optional[str] = None
    
    # Line settings
    line_channel_secret: Optional[str] = None
    line_channel_access_token: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        get_opik_url_override(self.environment)

    redis_config: dict = {
        "host": "127.0.0.1",
        "port": 6378,
        "db": 0,
        "password": os.getenv("REDIS_PASSWORD"),
        "max_connections": 10,
    }
    mongo_config: dict = {
        "uri": "mongodb://localhost:27017/",
        "db_name": os.getenv("MONGO_DATABASE"),
        "collection_name": os.getenv("MONGO_COLLECTION"),
        "username": os.getenv("MONGO_USERNAME"),
        "password": os.getenv("MONGO_PASSWORD"),
        "max_pool_size": 10,
    }
    mysql_config: dict = {
        "host": "127.0.0.1",
        "port": 3305,
        "username": "root",
        "password": os.getenv("MYSQL_ROOT_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False