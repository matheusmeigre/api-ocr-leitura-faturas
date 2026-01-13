from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # Upload
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf"  # Separado por vírgula: "pdf,jpg,png"
    
    # OCR
    paddle_ocr_lang: str = "pt"
    paddle_ocr_use_gpu: bool = False
    
    # Cache
    parser_cache_enabled: bool = True
    parser_cache_ttl_seconds: int = 3600  # 1 hora
    parser_cache_max_size: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def allowed_extensions_list(self) -> list[str]:
        """Retorna lista de extensões permitidas"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]


settings = Settings()
