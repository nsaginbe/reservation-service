import pydantic_settings
from dotenv import load_dotenv

load_dotenv()


class Config(pydantic_settings.BaseSettings):
    ACCESS_TOKENS: list[str] = ["test"]
    API_VERSION: str = "v1"
    ALLOWED_HOSTS: list[str] = ["*"]

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Merge all settings into a single dict for faster lookups
_settings = Config().model_dump()


def __getattr__(name):
    """Get configuration attribute by name."""
    if name in _settings:
        return _settings[name]
    raise AttributeError(f"Configuration attribute '{name}' not found")
