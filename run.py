"""
Script para iniciar o servidor de desenvolvimento
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando API de OCR e Extração de Dados Financeiros")
    print("=" * 60)
    print(f"📍 Host: {settings.api_host}")
    print(f"🔌 Porta: {settings.api_port}")
    print(f"🐛 Debug: {settings.api_debug}")
    print(f"📄 Documentação: http://localhost:{settings.api_port}/docs")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower()
    )
