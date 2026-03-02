from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    MINERU_API_KEY: str = ""
    MINERU_API_BASE_URL: str = "https://mineru.net"
    STORAGE_DIR: str = "./storage"
    TASK_POLL_INTERVAL: int = 3
    MAX_POLL_ATTEMPTS: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
