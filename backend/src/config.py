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

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./qbase_parse.db"
    # 工作区数据库：每个工作区有自己的 metadata.db
    WORKSPACE_DATABASE_NAME: str = "metadata.db"

    # 向量配置
    EMBEDDING_PROVIDER: str = "siliconflow"
    SILICONFLOW_EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    VECTOR_CHUNK_SIZE: int = 512
    VECTOR_CHUNK_OVERLAP: int = 128
    VECTOR_AUTO_INDEX: bool = False
    # LanceDB 存储到工作区的 .qbase/indexes/
    LANCEDB_USE_WORKSPACE: bool = True

    # .qbase 目录配置
    QBASE_DIR_NAME: str = ".qbase"
    GENERATED_DIR_NAME: str = "generated"
    INDEXES_DIR_NAME: str = "indexes"
    CACHE_DIR_NAME: str = "cache"
    CONFIG_FILE_NAME: str = "config.json"
    METADATA_DB_NAME: str = "metadata.db"

    class Config:
        env_file = ".env"


settings = Settings()
