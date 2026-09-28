from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
class Settings(BaseSettings):
    app_name: str = "Aletheia — CASE FILE"
    version: str = "4.0.0"
    environment: str = "production"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000"
    model_name: str = "MoritzLaurer/deberta-v3-base-zeroshot-v1.1"
    model_max_length: int = 512
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: float = 18.0
    chroma_path: str = str(BASE_DIR / "data" / "chroma")
    embedding_model: str = "all-MiniLM-L6-v2"
    max_web_results: int = 8
    max_trusted_results: int = 8
    cache_ttl_seconds: int = 300
    max_article_chars: int = 20000
    image_timeout_seconds: float = 8.0
    image_hash_threshold: int = 8
    model_config = SettingsConfigDict(env_file=(BASE_DIR/'.env'), env_file_encoding='utf-8', extra='ignore')
    @property
    def cors_list(self): return [x.strip() for x in self.cors_origins.split(',') if x.strip()]
@lru_cache
def get_settings(): return Settings()
