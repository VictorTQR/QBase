from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    MINERU_API_KEY: str = ""
    MINERU_API_BASE_URL: str = "https://mineru.net"
    STORAGE_DIR: str = "./storage"
    TASK_POLL_INTERVAL: int = 3
    MAX_POLL_ATTEMPTS: int = 60

    # 硅基流动配置
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_API_BASE_URL: str = "https://api.siliconflow.cn"
    SILICONFLOW_ASR_MODEL: str = "FunAudioLLM/SenseVoiceSmall"

    # 音频分块配置
    AUDIO_CHUNK_DURATION_MINUTES: int = 50
    AUDIO_MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
