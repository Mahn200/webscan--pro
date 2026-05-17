from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    database_url: str = "sqlite+aiosqlite:///./webscanpro.db"
    api_host: str = "127.0.0.1"
    api_port: int = 8765
    scan_timeout: int = 15
    max_retries: int = 3

    class Config:
        env_file = ".env"


settings = Settings()
