# Guia de Instalação e Deployment

Este documento detalha os passos para instalar e fazer deploy da API de OCR.

## 📋 Pré-requisitos

### Sistema Operacional

A API funciona em:
- ✅ Windows 10/11
- ✅ Linux (Ubuntu 20.04+, Debian, CentOS)
- ✅ macOS 11+

### Software Necessário

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonar o repositório)

### No Windows, você também precisa:
- Microsoft Visual C++ 14.0 ou superior (para algumas dependências)
- Poppler for Windows (para pdf2image)

### No Linux, instale as dependências do sistema:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
sudo apt-get install -y poppler-utils
```

## 🚀 Instalação Local (Desenvolvimento)

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd api-ocr-leitura-faturas
```

### 2. Crie e ative o ambiente virtual

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota:** A instalação pode levar alguns minutos, especialmente o PaddleOCR.

### 4. Configure as variáveis de ambiente

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edite o arquivo `.env` conforme necessário.

### 5. Inicie o servidor

**Opção 1 - Script de inicialização:**
```bash
python run.py
```

**Opção 2 - Diretamente com uvicorn:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Opção 3 - Com o main.py:**
```bash
python main.py
```

### 6. Teste a API

Acesse: http://localhost:8000/docs

Ou teste com cURL:
```bash
curl http://localhost:8000/health
```

## 🐳 Deploy com Docker

### Dockerfile

Crie um arquivo `Dockerfile` na raiz do projeto:

```dockerfile
FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Expõe a porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api-ocr:
    build: .
    container_name: api-ocr-faturas
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - API_DEBUG=False
      - LOG_LEVEL=INFO
    volumes:
      - ./temp:/app/temp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Build e execução

```bash
# Build da imagem
docker build -t api-ocr-faturas .

# Executar container
docker run -d -p 8000:8000 --name api-ocr api-ocr-faturas

# Ou com docker-compose
docker-compose up -d
```

### Verificar logs

```bash
docker logs -f api-ocr
```

## ☁️ Deploy em Cloud

### Deploy no Heroku

1. Crie um `Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Crie `runtime.txt`:

```
python-3.10.12
```

3. Ajuste `requirements.txt` para incluir gunicorn:

```
gunicorn==21.2.0
```

4. Deploy:

```bash
heroku login
heroku create nome-da-sua-api
git push heroku main
```

### Deploy no AWS EC2

1. Conecte via SSH:

```bash
ssh -i sua-chave.pem ubuntu@seu-ip
```

2. Instale dependências:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 poppler-utils
```

3. Clone e configure:

```bash
git clone <seu-repositorio>
cd api-ocr-leitura-faturas
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Configure como serviço systemd:

Crie `/etc/systemd/system/api-ocr.service`:

```ini
[Unit]
Description=API OCR Leitura Faturas
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/api-ocr-leitura-faturas
Environment="PATH=/home/ubuntu/api-ocr-leitura-faturas/venv/bin"
ExecStart=/home/ubuntu/api-ocr-leitura-faturas/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

5. Inicie o serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable api-ocr
sudo systemctl start api-ocr
sudo systemctl status api-ocr
```

6. Configure nginx como proxy reverso:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Aumenta timeout para processar PDFs grandes
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
        
        # Aumenta tamanho máximo de upload
        client_max_body_size 10M;
    }
}
```

### Deploy no Google Cloud Run

1. Crie `cloudbuild.yaml`:

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/api-ocr-faturas', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/api-ocr-faturas']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'api-ocr-faturas'
      - '--image'
      - 'gcr.io/$PROJECT_ID/api-ocr-faturas'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '2Gi'
      - '--timeout'
      - '300'
      - '--max-instances'
      - '10'
```

2. Deploy:

```bash
gcloud builds submit --config cloudbuild.yaml
```

## 🔒 Segurança em Produção

### 1. Configure HTTPS

Use certbot para SSL gratuito:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

### 2. Atualize CORS

No [main.py](main.py), restrinja os domínios permitidos:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seu-frontend.com",
        "https://www.seu-frontend.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 3. Configure rate limiting

Instale:
```bash
pip install slowapi
```

Adicione ao `main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/extract")
@limiter.limit("10/minute")  # 10 requisições por minuto
async def extract_financial_data(...):
    ...
```

### 4. Configure autenticação (opcional)

Para API Key:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY = "sua-chave-secreta"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return api_key

@app.post("/extract")
async def extract_financial_data(
    file: UploadFile,
    api_key: str = Depends(verify_api_key)
):
    ...
```

## 📊 Monitoramento

### 1. Logs

Configuração de logs estruturados:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
```

### 2. Health check endpoint

Já implementado em `/health`, use para monitoramento:

```bash
# Cron job para verificar a cada 5 minutos
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart api-ocr
```

### 3. Métricas com Prometheus (opcional)

Instale:
```bash
pip install prometheus-fastapi-instrumentator
```

Adicione ao `main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)

Instrumentator().instrument(app).expose(app)
```

Acesse métricas em: `http://localhost:8000/metrics`

## ⚡ Otimização de Performance

### 1. Use workers múltiplos

```bash
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

### 2. Configure cache para OCR

No `extractors/text_extractor.py`, implemente cache com Redis:

```python
import redis
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_text(pdf_bytes):
    key = hashlib.md5(pdf_bytes).hexdigest()
    cached = redis_client.get(key)
    if cached:
        return cached.decode('utf-8')
    return None

def cache_text(pdf_bytes, text):
    key = hashlib.md5(pdf_bytes).hexdigest()
    redis_client.setex(key, 3600, text)  # Cache por 1 hora
```

### 3. Ajuste timeouts

No `.env`:
```env
WORKER_TIMEOUT=300
KEEPALIVE_TIMEOUT=5
```

## 🧪 Testes

### Teste manual

```bash
python test_api.py documento.pdf
```

### Teste automatizado

Crie `tests/test_api.py`:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_extract():
    with open("test.pdf", "rb") as f:
        response = client.post(
            "/extract",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    assert response.status_code == 200
    assert response.json()["success"] == True
```

Execute:
```bash
pip install pytest
pytest tests/
```

## 🆘 Troubleshooting

### Erro: "No module named 'paddleocr'"

```bash
pip install paddleocr paddlepaddle
```

### Erro: "libGL.so.1: cannot open shared object file"

```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-glx

# CentOS
sudo yum install mesa-libGL
```

### Erro: "Unable to find poppler"

**Windows:**
1. Baixe Poppler: https://github.com/oschwartz10612/poppler-windows/releases
2. Extraia e adicione ao PATH
3. Ou configure no código:
```python
from pdf2image import convert_from_bytes
images = convert_from_bytes(pdf_bytes, poppler_path=r"C:\poppler\bin")
```

**Linux:**
```bash
sudo apt-get install poppler-utils
```

### Performance lenta

1. Use GPU para OCR (se disponível)
2. Reduza DPI da conversão de PDF para imagem
3. Implemente cache
4. Use workers múltiplos

## 📞 Suporte

Para problemas:
1. Verifique os logs: `docker logs api-ocr` ou `journalctl -u api-ocr`
2. Teste o health check: `curl http://localhost:8000/health`
3. Verifique a documentação: `http://localhost:8000/docs`

---

**Última atualização:** Janeiro 2026
