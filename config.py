from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # Upload
    max_file_size_mb: int = 10
    allowed_extensions: List[str] = ["pdf"]
    
    # OCR
    paddle_ocr_lang: str = "pt"
    paddle_ocr_use_gpu: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
