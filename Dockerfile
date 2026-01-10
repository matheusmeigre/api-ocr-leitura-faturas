FROM python:3.10-slim

# Define metadata
LABEL maintainer="API OCR Leitura Faturas"
LABEL version="1.0.0"

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para OpenCV, PaddleOCR e pdf2image
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .

# Atualiza pip e instala dependências
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretório para arquivos temporários
RUN mkdir -p /app/temp/uploads

# Define variáveis de ambiente padrão
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV API_DEBUG=False
ENV PYTHONUNBUFFERED=1

# Expõe a porta da API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando de inicialização com múltiplos workers para produção
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
